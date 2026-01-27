import React from 'react';
import type { Skill, RegistrySkill } from '../../../domain/entities/types';

interface SkillCardProps {
    skill: Skill | RegistrySkill;
    onInstall?: (skill: RegistrySkill) => void;
    onUninstall?: (skill: Skill) => void;
    installed?: boolean;
}

export const SkillCard: React.FC<SkillCardProps> = ({ skill, onInstall, onUninstall, installed }) => {
    const version = 'latest_version' in skill ? skill.latest_version : skill.version;
    const isRegistry = 'latest_version' in skill;

    return (
        <div className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <div className="flex justify-between items-start">
                <div>
                    <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">{skill.name || skill.id}</h3>
                    <p className="text-sm text-gray-500 font-mono">v{version}</p>
                </div>
                {installed ? (
                    <span className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100 text-xs px-2 py-1 rounded-full">Installed</span>
                ) : (
                    <span className="bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100 text-xs px-2 py-1 rounded-full">Available</span>
                )}
            </div>

            <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 line-clamp-2 min-h-[2.5rem]">
                {skill.description}
            </p>

            {isRegistry && 'tags' in skill && (
                <div className="mt-3 flex gap-1 flex-wrap">
                    {(skill as RegistrySkill).tags?.map(tag => (
                        <span key={tag} className="bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 text-xs px-2 py-0.5 rounded">
                            {tag}
                        </span>
                    ))}
                </div>
            )}

            <div className="mt-4 flex gap-2">
                {onInstall && !installed && (
                    <button
                        onClick={() => onInstall(skill as RegistrySkill)}
                        className="px-3 py-1.5 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors w-full"
                    >
                        Install
                    </button>
                )}
                {onUninstall && installed && (
                    <button
                        onClick={() => onUninstall(skill as Skill)}
                        className="px-3 py-1.5 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-100 text-sm rounded hover:bg-red-200 dark:hover:bg-red-800 transition-colors w-full"
                    >
                        Uninstall
                    </button>
                )}
            </div>
        </div>
    );
};
