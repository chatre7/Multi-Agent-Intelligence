
import { useState } from "react";
import { Save } from "lucide-react";
import type { DomainConfig } from "../../../domain/entities/types";

interface DomainConfigurationProps {
    domain: DomainConfig;
}

export function DomainConfiguration({ domain }: DomainConfigurationProps) {
    const [config] = useState(domain.metadata || {});
    const [workflowType, setWorkflowType] = useState(domain.workflow_type || "supervisor");
    const [isDirty, setIsDirty] = useState(false);

    // Workflow options
    const workflowTypes = [
        { value: "supervisor", label: "Supervisor (Legacy)" },
        { value: "orchestrator", label: "Orchestrator (Sequential)" },
        { value: "few_shot", label: "Few-Shot (LLM Router)" },
        { value: "hybrid", label: "Hybrid (Mixed)" },
    ];

    const handleSave = () => {
        console.log("Saving config:", { workflow_type: workflowType, metadata: config });
        alert("Configuration update simulation. Backend endpoint not implemented yet.");
        setIsDirty(false);
    };

    const renderOrchestratorConfig = () => {
        const pipeline = config.orchestration?.pipeline || [];
        return (
            <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Orchestration Pipeline</h4>
                <p className="text-sm text-gray-500">
                    Define the sequence of agents to execute.
                </p>
                <div className="space-y-2">
                    {pipeline.length === 0 && <p className="text-sm text-gray-400 italic">No agents in pipeline</p>}
                    {pipeline.map((agentId: string, idx: number) => (
                        <div key={idx} className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200">
                            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded font-mono">{idx + 1}</span>
                            <span className="text-sm font-medium">{agentId}</span>
                        </div>
                    ))}
                </div>
                <div className="text-xs text-yellow-600 bg-yellow-50 p-2 rounded">
                    To edit pipeline, please modify the domain YAML file directly.
                </div>
            </div>
        );
    };

    const renderFewShotConfig = () => {
        const fewShot = config.few_shot || {};
        const examples = fewShot.routing_examples || [];

        return (
            <div className="space-y-6">
                <div>
                    <label className="block text-sm font-medium text-gray-700">Max Handoffs</label>
                    <input
                        type="number"
                        value={fewShot.max_handoffs || 5}
                        disabled
                        className="mt-1 block w-24 rounded-md border-gray-300 bg-gray-100 shadow-sm sm:text-sm"
                    />
                </div>

                <div>
                    <h4 className="font-medium text-gray-900 mb-2">Routing Examples</h4>
                    {examples.length === 0 ? (
                        <p className="text-sm text-gray-400 italic">No custom examples defined (using defaults).</p>
                    ) : (
                        <div className="space-y-3">
                            {examples.map((ex: any, idx: number) => (
                                <div key={idx} className="border border-gray-200 rounded-lg p-3 bg-white">
                                    <div className="mb-2">
                                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Situation</span>
                                        <p className="text-sm text-gray-900 mt-1">{ex.situation}</p>
                                    </div>
                                    <div>
                                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Decision</span>
                                        <pre className="text-xs bg-gray-50 p-2 rounded mt-1 overflow-x-auto">
                                            {JSON.stringify(ex.decision, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                    <div className="mt-2 text-xs text-yellow-600 bg-yellow-50 p-2 rounded">
                        To add examples, please modify the domain YAML file directly.
                        <br />
                        <code>few_shot: routing_examples: [...]</code>
                    </div>
                </div>
            </div>
        );
    };

    const renderHybridConfig = () => {
        const hybrid = config.hybrid || {};
        return (
            <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div className="border rounded p-4">
                        <h5 className="font-medium text-purple-700 mb-2">Orchestrator Decides</h5>
                        <ul className="list-disc pl-4 text-sm text-gray-600">
                            {hybrid.orchestrator_decides?.map((phase: string) => <li key={phase}>{phase}</li>) || <li>None</li>}
                        </ul>
                    </div>
                    <div className="border rounded p-4">
                        <h5 className="font-medium text-indigo-700 mb-2">LLM Decides</h5>
                        <ul className="list-disc pl-4 text-sm text-gray-600">
                            {hybrid.llm_decides?.map((phase: string) => <li key={phase}>{phase}</li>) || <li>None</li>}
                        </ul>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Workflow Configuration</h3>
                {isDirty && (
                    <button
                        onClick={handleSave}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
                    >
                        <Save size={16} />
                        Save Changes
                    </button>
                )}
            </div>

            <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Strategy Type</label>
                    <div className="flex flex-wrap gap-2">
                        {workflowTypes.map(type => (
                            <button
                                key={type.value}
                                onClick={() => {
                                    setWorkflowType(type.value);
                                    setIsDirty(true);
                                }}
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${workflowType === type.value
                                    ? 'bg-blue-100 text-blue-800 border-blue-200 border'
                                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                                    }`}
                            >
                                {type.label}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="border-t border-gray-100 pt-6">
                    {workflowType === 'orchestrator' && renderOrchestratorConfig()}
                    {workflowType === 'few_shot' && renderFewShotConfig()}
                    {workflowType === 'hybrid' && renderHybridConfig()}
                    {workflowType === 'supervisor' && <p className="text-gray-500 text-sm">Using standard supervisor routing logic based on keywords.</p>}
                </div>
            </div>
        </div>
    );
}
