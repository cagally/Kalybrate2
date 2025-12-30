import React from 'react';

const gradeColors = {
  A: 'bg-green-500',
  B: 'bg-blue-500',
  C: 'bg-yellow-500',
  D: 'bg-orange-500',
  F: 'bg-red-500',
};

const SkillCard = ({ skill }) => {
  const {
    skill_name,
    overall_score,
    grade,
    task_pass_rate,
    selectivity_rate,
    quality_improvement_rate,
    tasks_passed,
    total_tasks,
    selectivity_passed,
    total_selectivity_tests,
  } = skill;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
            {skill_name}
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            AI Agent Skill
          </p>
        </div>
        <div className={`${gradeColors[grade]} text-white text-2xl font-bold rounded-full w-14 h-14 flex items-center justify-center`}>
          {grade}
        </div>
      </div>

      {/* Overall Score */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Overall Score
          </span>
          <span className="text-lg font-bold text-gray-900 dark:text-white">
            {overall_score.toFixed(1)}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className={`${gradeColors[grade]} h-2 rounded-full transition-all`}
            style={{ width: `${overall_score}%` }}
          />
        </div>
      </div>

      {/* Metrics */}
      <div className="space-y-3">
        {/* Task Completion */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-600 dark:text-gray-400">
              Task Completion
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {(task_pass_rate * 100).toFixed(0)}% ({tasks_passed}/{total_tasks})
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className="bg-blue-500 h-1.5 rounded-full"
              style={{ width: `${task_pass_rate * 100}%` }}
            />
          </div>
        </div>

        {/* Selectivity */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-600 dark:text-gray-400">
              Selectivity
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {(selectivity_rate * 100).toFixed(0)}% ({selectivity_passed}/{total_selectivity_tests})
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className="bg-purple-500 h-1.5 rounded-full"
              style={{ width: `${selectivity_rate * 100}%` }}
            />
          </div>
        </div>

        {/* Quality Improvement */}
        <div>
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs text-gray-600 dark:text-gray-400">
              Quality Improvement
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {(quality_improvement_rate * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className="bg-green-500 h-1.5 rounded-full"
              style={{ width: `${quality_improvement_rate * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SkillCard;
