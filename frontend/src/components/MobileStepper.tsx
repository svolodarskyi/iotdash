interface MobileStepperProps {
  currentStep: number
  totalSteps: number
  stepLabels?: string[]
}

export function MobileStepper({ currentStep, totalSteps, stepLabels }: MobileStepperProps) {
  return (
    <div className="mb-6">
      {/* Progress dots */}
      <div className="flex justify-center gap-2 mb-2">
        {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
          <div
            key={step}
            className={`h-2 flex-1 max-w-[60px] rounded-full transition-colors ${
              step <= currentStep ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          />
        ))}
      </div>

      {/* Step label */}
      {stepLabels && stepLabels[currentStep - 1] && (
        <p className="text-center text-sm font-medium text-gray-700">
          Step {currentStep} of {totalSteps}: {stepLabels[currentStep - 1]}
        </p>
      )}
    </div>
  )
}
