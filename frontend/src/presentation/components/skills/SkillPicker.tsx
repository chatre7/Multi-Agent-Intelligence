import React, { useState } from 'react';
import type { Skill, RegistrySkill } from '../../../domain/entities/types';
import { SkillCard } from './SkillCard';
import { apiClient } from '../../../infrastructure/api/apiClient';

interface SkillPickerProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (skillId: string) => void;
    installedSkills: Skill[];
    availableSkills: RegistrySkill[];
}

export const SkillPicker: React.FC<SkillPickerProps> = ({
    isOpen,
    onClose,
    onSelect,
    installedSkills,
    availableSkills
}) => {
    const [search, setSearch] = useState('');
    const [tab, setTab] = useState<'installed' | 'marketplace' | 'import'>('installed');
    const [importUrl, setImportUrl] = useState('');
    const [isImporting, setIsImporting] = useState(false);

    if (!isOpen) return null;

    const handleImport = async () => {
        if (!importUrl) return;
        setIsImporting(true);
        try {
            const skill = await apiClient.importSkill(importUrl);
            console.log(`Successfully imported skill: ${skill.name}`);
            setImportUrl('');
            setTab('installed');
            // Notify parent if possible, or just refresh
            window.location.reload();
        } catch (error: any) {
            console.error(error);
        } finally {
            setIsImporting(false);
        }
    };

    const filteredInstalled = installedSkills.filter(s =>
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.description.toLowerCase().includes(search.toLowerCase())
    );

    const filteredAvailable = availableSkills.filter(s =>
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.description.toLowerCase().includes(search.toLowerCase()) ||
        s.tags.some(t => t.toLowerCase().includes(search.toLowerCase()))
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-xl w-full max-w-5xl max-h-[85vh] flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700">

                {/* Header */}
                <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center bg-white dark:bg-gray-900">
                    <h2 className="text-xl font-bold dark:text-white">Skill Library</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Toolbar */}
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 flex flex-col sm:flex-row gap-4 border-b border-gray-200 dark:border-gray-800">
                    <div className="flex bg-white dark:bg-gray-800 rounded-lg p-1 border border-gray-200 dark:border-gray-700 shadow-sm">
                        <button
                            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === 'installed' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            onClick={() => setTab('installed')}
                        >
                            My Skills
                        </button>
                        <button
                            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === 'marketplace' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            onClick={() => setTab('marketplace')}
                        >
                            Marketplace
                        </button>
                        <button
                            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === 'import' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-100 shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'}`}
                            onClick={() => setTab('import')}
                        >
                            Import
                        </button>
                    </div>

                    <div className="relative flex-1">
                        <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
                        <input
                            type="text"
                            placeholder="Search skills by name, tag, or description..."
                            className="w-full pl-10 pr-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                {/* Tag Filters */}
                <div className="px-4 py-2 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 flex gap-2 overflow-x-auto no-scrollbar">
                    {['All', 'Engineering', 'Research', 'Creative', 'Architecture', 'AI'].map(tag => (
                        <button
                            key={tag}
                            onClick={() => setSearch(tag === 'All' ? '' : tag)}
                            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors whitespace-nowrap ${(search === tag || (tag === 'All' && !search))
                                ? 'bg-gray-900 text-white dark:bg-white dark:text-black'
                                : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400 hover:bg-gray-200'
                                }`}
                        >
                            {tag}
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-black/20">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {tab === 'installed' ? (
                            filteredInstalled.length > 0 ? (
                                filteredInstalled.map(skill => (
                                    <div key={skill.id} className="relative group">
                                        <SkillCard skill={skill} installed={true} />
                                        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => onSelect(skill.id)}
                                                className="bg-blue-600 text-white text-xs px-2 py-1 rounded shadow-lg hover:bg-blue-700"
                                            >
                                                Select
                                            </button>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-full flex flex-col items-center justify-center py-16 text-gray-500 dark:text-gray-400">
                                    <div className="text-4xl mb-4">📦</div>
                                    <p className="text-lg font-medium">No installed skills found</p>
                                    <p className="text-sm">Check the Marketplace tab to discover new skills.</p>
                                </div>
                            )
                        ) : (
                            filteredAvailable.length > 0 ? (
                                filteredAvailable.map(skill => (
                                    <div key={skill.id}>
                                        <SkillCard
                                            skill={skill}
                                            installed={installedSkills.some(i => i.id === skill.id)}
                                            onInstall={() => alert(`Installing ${skill.name}... (Simulated)`)}
                                        />
                                    </div>
                                ))
                            ) : (
                                <div className="col-span-full flex flex-col items-center justify-center py-16 text-gray-500 dark:text-gray-400">
                                    <div className="text-4xl mb-4">🔍</div>
                                    <p className="text-lg font-medium">No skills found</p>
                                    <p className="text-sm">Try adjusting your search query.</p>
                                </div>
                            )
                        )}
                        {tab === 'import' && (
                            <div className="col-span-full flex flex-col items-center justify-center py-12">
                                <div className="w-full max-w-lg space-y-4 bg-white dark:bg-gray-800 p-8 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                                    <div>
                                        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Import from GitHub</h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                            Enter the URL of a GitHub repository containing a SKILL.md file.
                                        </p>
                                    </div>

                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                            Repository URL
                                        </label>
                                        <input
                                            type="text"
                                            placeholder="https://github.com/username/my-awesome-skill"
                                            className="w-full px-4 py-2 border rounded-lg dark:bg-gray-900 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                            value={importUrl}
                                            onChange={e => setImportUrl(e.target.value)}
                                        />
                                    </div>

                                    <div className="pt-2">
                                        <button
                                            onClick={handleImport}
                                            disabled={!importUrl || isImporting}
                                            className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                        >
                                            {isImporting ? (
                                                <>
                                                    <span className="animate-spin">⟳</span> Importing...
                                                </>
                                            ) : (
                                                'Import Skill'
                                            )}
                                        </button>
                                    </div>

                                    <p className="text-xs text-gray-500 border-t border-gray-200 dark:border-gray-700 pt-4 mt-4">
                                        Note: The repository must be public or accessible by the system.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors font-medium border border-gray-200 dark:border-gray-700"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};
