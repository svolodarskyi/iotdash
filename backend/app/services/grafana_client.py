"""Grafana Alerting API client.

Wraps Grafana's provisioning API for managing alert rules,
contact points, and notification policies.
"""

from __future__ import annotations

import logging
import uuid

import httpx
from fastapi import HTTPException

from app.config import settings
from app.models import Alert, DeviceProvisioned, Organisation

logger = logging.getLogger(__name__)

ALERTS_FOLDER_TITLE = "iotdash-alerts"
RULE_GROUP = "iotdash-alerts"
EVAL_INTERVAL = "1m"


class GrafanaClient:
    def __init__(
        self,
        base_url: str = settings.GRAFANA_URL,
        admin_user: str = settings.GRAFANA_ADMIN_USER,
        admin_password: str = settings.GRAFANA_ADMIN_PASSWORD,
    ):
        self.base_url = base_url.rstrip("/")
        self.auth = (admin_user, admin_password)

    # ── helpers ────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> dict | list | None:
        url = f"{self.base_url}{path}"
        headers = {"X-Disable-Provenance": "true"}
        try:
            resp = httpx.request(
                method,
                url,
                auth=self.auth,
                json=json,
                headers=headers,
                timeout=15.0,
            )
        except httpx.HTTPError as exc:
            logger.error("Grafana request failed: %s %s — %s", method, path, exc)
            raise HTTPException(status_code=502, detail=f"Grafana unreachable: {exc}")

        if resp.status_code not in expected:
            detail = resp.text[:500]
            logger.error(
                "Grafana API error: %s %s → %s %s",
                method,
                path,
                resp.status_code,
                detail,
            )
            raise HTTPException(
                status_code=502,
                detail=f"Grafana API error ({resp.status_code}): {detail}",
            )

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ── org provisioning ────────────────────────────────

    def create_org(self, name: str) -> int:
        """Create a Grafana organisation. Returns the Grafana org ID."""
        result = self._request(
            "POST",
            "/api/orgs",
            json={"name": name},
            expected=(200,),
        )
        return result["orgId"]

    def add_datasource_to_org(self, org_id: int) -> None:
        """Create the InfluxDB datasource inside a Grafana org."""
        from app.config import settings

        ds_body = {
            "name": "InfluxDB",
            "type": "influxdb",
            "access": "proxy",
            "url": settings.INFLUXDB_URL,
            "jsonData": {
                "defaultBucket": settings.INFLUXDB_BUCKET,
                "httpMode": "POST",
                "organization": settings.INFLUXDB_ORG,
                "version": "Flux",
            },
            "secureJsonData": {
                "token": settings.INFLUXDB_TOKEN,
            },
        }
        self._org_request("POST", "/api/datasources", org_id, json=ds_body, expected=(200,))

    def create_dashboard_in_org(self, org_id: int, dashboard_json: dict) -> str:
        """Create a dashboard inside a Grafana org. Returns the dashboard UID."""
        body = {
            "dashboard": dashboard_json,
            "overwrite": True,
        }
        result = self._org_request("POST", "/api/dashboards/db", org_id, json=body, expected=(200,))
        return result["uid"]

    def _org_request(
        self,
        method: str,
        path: str,
        org_id: int,
        *,
        json: dict | list | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> dict | list | None:
        """Like _request but with X-Grafana-Org-Id header for org-scoped operations."""
        url = f"{self.base_url}{path}"
        headers = {
            "X-Disable-Provenance": "true",
            "X-Grafana-Org-Id": str(org_id),
        }
        try:
            resp = httpx.request(
                method,
                url,
                auth=self.auth,
                json=json,
                headers=headers,
                timeout=15.0,
            )
        except httpx.HTTPError as exc:
            logger.error("Grafana request failed: %s %s — %s", method, path, exc)
            raise HTTPException(status_code=502, detail=f"Grafana unreachable: {exc}")

        if resp.status_code not in expected:
            detail = resp.text[:500]
            logger.error(
                "Grafana API error: %s %s → %s %s",
                method,
                path,
                resp.status_code,
                detail,
            )
            raise HTTPException(
                status_code=502,
                detail=f"Grafana API error ({resp.status_code}): {detail}",
            )

        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ── folders ────────────────────────────────────────

    def ensure_alerts_folder(self) -> str:
        """Get or create the iotdash-alerts folder. Returns folder UID."""
        folders = self._request("GET", "/api/folders")
        for f in folders:
            if f.get("title") == ALERTS_FOLDER_TITLE:
                return f["uid"]

        result = self._request(
            "POST",
            "/api/folders",
            json={"title": ALERTS_FOLDER_TITLE},
            expected=(200,),
        )
        return result["uid"]

    # ── datasource ─────────────────────────────────────

    def get_datasource_uid(self) -> str:
        """Look up the InfluxDB datasource UID from Grafana."""
        datasources = self._request("GET", "/api/datasources")
        for ds in datasources:
            if ds.get("type") == "influxdb":
                return ds["uid"]
        raise HTTPException(
            status_code=502,
            detail="No InfluxDB datasource found in Grafana",
        )

    # ── alert rules ────────────────────────────────────

    def _build_rule_body(
        self,
        alert: Alert,
        device: DeviceProvisioned,
        org: Organisation,
        folder_uid: str,
        *,
        existing_uid: str | None = None,
        is_paused: bool = False,
    ) -> dict:
        ds_uid = self.get_datasource_uid()
        duration_str = f"{alert.duration_seconds}s"

        condition_type = "gt" if alert.condition == "above" else "lt"

        flux_query = (
            f'from(bucket: "iot")'
            f" |> range(start: -{duration_str})"
            f' |> filter(fn: (r) => r.device_id == "{device.device_code}")'
            f' |> filter(fn: (r) => r._field == "{alert.metric}")'
            f" |> last()"
        )

        rule = {
            "folderUID": folder_uid,
            "ruleGroup": RULE_GROUP,
            "title": f"{device.device_code} — {alert.metric} {alert.condition} {alert.threshold}",
            "condition": "C",
            "labels": {
                "iotdash_alert_id": str(alert.id),
                "device_code": device.device_code,
            },
            "annotations": {
                "summary": (
                    f"Device {device.device_code}: {alert.metric} is "
                    f"{alert.condition} {alert.threshold}"
                ),
            },
            "noDataState": "NoData",
            "execErrState": "Error",
            "isPaused": is_paused,
            "for": duration_str,
            "data": [
                {
                    "refId": "A",
                    "relativeTimeRange": {"from": alert.duration_seconds, "to": 0},
                    "datasourceUid": ds_uid,
                    "model": {
                        "refId": "A",
                        "query": flux_query,
                        "intervalMs": 1000,
                        "maxDataPoints": 43200,
                    },
                },
                {
                    "refId": "B",
                    "relativeTimeRange": {"from": 0, "to": 0},
                    "datasourceUid": "__expr__",
                    "model": {
                        "refId": "B",
                        "type": "reduce",
                        "expression": "A",
                        "reducer": "last",
                    },
                },
                {
                    "refId": "C",
                    "relativeTimeRange": {"from": 0, "to": 0},
                    "datasourceUid": "__expr__",
                    "model": {
                        "refId": "C",
                        "type": "threshold",
                        "expression": "B",
                        "conditions": [
                            {
                                "evaluator": {
                                    "type": condition_type,
                                    "params": [alert.threshold],
                                },
                            }
                        ],
                    },
                },
            ],
        }

        if existing_uid:
            rule["uid"] = existing_uid

        return rule

    def create_alert_rule(
        self,
        alert: Alert,
        device: DeviceProvisioned,
        org: Organisation,
        folder_uid: str,
    ) -> str:
        """Create a Grafana alert rule. Returns the rule UID."""
        body = self._build_rule_body(alert, device, org, folder_uid)
        result = self._request(
            "POST",
            "/api/v1/provisioning/alert-rules",
            json=body,
            expected=(201,),
        )
        return result["uid"]

    def update_alert_rule(
        self,
        grafana_rule_uid: str,
        alert: Alert,
        device: DeviceProvisioned,
        org: Organisation,
        folder_uid: str,
        *,
        is_paused: bool = False,
    ) -> None:
        """Update an existing Grafana alert rule."""
        body = self._build_rule_body(
            alert,
            device,
            org,
            folder_uid,
            existing_uid=grafana_rule_uid,
            is_paused=is_paused,
        )
        self._request(
            "PUT",
            f"/api/v1/provisioning/alert-rules/{grafana_rule_uid}",
            json=body,
            expected=(200,),
        )

    def delete_alert_rule(self, grafana_rule_uid: str) -> None:
        """Delete a Grafana alert rule."""
        self._request(
            "DELETE",
            f"/api/v1/provisioning/alert-rules/{grafana_rule_uid}",
            expected=(204,),
        )

    # ── contact points ─────────────────────────────────

    def _contact_point_name(self, alert_id: uuid.UUID) -> str:
        return f"alert-{alert_id}"

    def ensure_contact_point(self, alert: Alert) -> None:
        """Create or update the email contact point for an alert."""
        name = self._contact_point_name(alert.id)
        body = {
            "name": name,
            "type": "email",
            "settings": {
                "addresses": alert.notification_email,
                "singleEmail": True,
            },
        }

        # Check if contact point already exists
        existing = self._request("GET", "/api/v1/provisioning/contact-points")
        for cp in existing:
            if cp.get("name") == name:
                self._request(
                    "PUT",
                    f"/api/v1/provisioning/contact-points/{cp['uid']}",
                    json=body,
                    expected=(202,),
                )
                return

        self._request(
            "POST",
            "/api/v1/provisioning/contact-points",
            json=body,
            expected=(202,),
        )

    def delete_contact_point(self, alert_id: uuid.UUID) -> None:
        """Delete the contact point for an alert."""
        name = self._contact_point_name(alert_id)
        existing = self._request("GET", "/api/v1/provisioning/contact-points")
        for cp in existing:
            if cp.get("name") == name:
                self._request(
                    "DELETE",
                    f"/api/v1/provisioning/contact-points/{cp['uid']}",
                    expected=(202,),
                )
                return

    # ── notification policies ──────────────────────────

    def ensure_notification_policy(self, alert: Alert) -> None:
        """Add a notification policy route for this alert."""
        cp_name = self._contact_point_name(alert.id)
        alert_label = str(alert.id)

        policy = self._request("GET", "/api/v1/provisioning/policies")
        routes = policy.get("routes") or []

        # Check if route already exists
        for route in routes:
            matchers = route.get("object_matchers") or []
            for m in matchers:
                if len(m) == 3 and m[0] == "iotdash_alert_id" and m[2] == alert_label:
                    # Already exists — update receiver
                    route["receiver"] = cp_name
                    self._request(
                        "PUT",
                        "/api/v1/provisioning/policies",
                        json=policy,
                        expected=(202,),
                    )
                    return

        # Add new route
        routes.append(
            {
                "receiver": cp_name,
                "object_matchers": [["iotdash_alert_id", "=", alert_label]],
                "continue": False,
            }
        )
        policy["routes"] = routes
        self._request(
            "PUT",
            "/api/v1/provisioning/policies",
            json=policy,
            expected=(202,),
        )

    def remove_notification_policy(self, alert_id: uuid.UUID) -> None:
        """Remove the notification policy route for this alert."""
        alert_label = str(alert_id)

        policy = self._request("GET", "/api/v1/provisioning/policies")
        routes = policy.get("routes") or []

        new_routes = []
        for route in routes:
            matchers = route.get("object_matchers") or []
            match = any(
                len(m) == 3 and m[0] == "iotdash_alert_id" and m[2] == alert_label
                for m in matchers
            )
            if not match:
                new_routes.append(route)

        if len(new_routes) != len(routes):
            policy["routes"] = new_routes
            self._request(
                "PUT",
                "/api/v1/provisioning/policies",
                json=policy,
                expected=(202,),
            )


def get_grafana_client() -> GrafanaClient:
    """Factory for dependency injection."""
    return GrafanaClient()
