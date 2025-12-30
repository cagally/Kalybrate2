import { useState, useMemo } from 'react';
import SkillCard from './components/SkillCard';
import skillsData from './data/skills.json';
import './index.css';

function App() {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('overall_score');
  const [filterGrade, setFilterGrade] = useState('all');

  // Filter and sort skills
  const filteredSkills = useMemo(() => {
    let filtered = skillsData;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(skill =>
        skill.skill_name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Grade filter
    if (filterGrade !== 'all') {
      filtered = filtered.filter(skill => skill.grade === filterGrade);
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      if (sortBy === 'overall_score') {
        return b.overall_score - a.overall_score;
      } else if (sortBy === 'name') {
        return a.skill_name.localeCompare(b.skill_name);
      } else if (sortBy === 'task_pass_rate') {
        return b.task_pass_rate - a.task_pass_rate;
      }
      return 0;
    });

    return filtered;
  }, [searchTerm, sortBy, filterGrade]);

  // Calculate stats
  const stats = useMemo(() => {
    const total = skillsData.length;
    const avgScore = skillsData.reduce((sum, s) => sum + s.overall_score, 0) / total;
    const gradeA = skillsData.filter(s => s.grade === 'A').length;

    return { total, avgScore, gradeA };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Kalybrate
              </h1>
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                AI Agent Skill Ratings - G2 for AI Tools
              </p>
            </div>
            <div className="flex gap-4 text-center">
              <div className="px-4">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.total}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Total Skills
                </div>
              </div>
              <div className="px-4 border-l border-gray-300 dark:border-gray-600">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.avgScore.toFixed(1)}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Avg Score
                </div>
              </div>
              <div className="px-4 border-l border-gray-300 dark:border-gray-600">
                <div className="text-2xl font-bold text-green-500">
                  {stats.gradeA}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Grade A
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Controls */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search skills..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Sort */}
          <div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="overall_score">Sort by Score</option>
              <option value="name">Sort by Name</option>
              <option value="task_pass_rate">Sort by Task Pass Rate</option>
            </select>
          </div>

          {/* Filter */}
          <div>
            <select
              value={filterGrade}
              onChange={(e) => setFilterGrade(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Grades</option>
              <option value="A">Grade A</option>
              <option value="B">Grade B</option>
              <option value="C">Grade C</option>
              <option value="D">Grade D</option>
              <option value="F">Grade F</option>
            </select>
          </div>
        </div>
      </div>

      {/* Skills Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        {filteredSkills.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              No skills found matching your criteria.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSkills.map((skill) => (
              <SkillCard key={skill.skill_name} skill={skill} />
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-600 dark:text-gray-400">
            Kalybrate - Objective ratings for AI agent skills
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
