import React from 'react';

const ReusableTable = ({
  headers = [],
  data = [],
  renderRow,
  noDataMessage = 'No data available',
  className = ''
}) => {
  return (
    <div className={`overflow-x-auto bg-white shadow-lg rounded-2xl p-6 border border-gray-400 ${className}`}>
      <table className="min-w-full text-sm text-left border-separate border-spacing-y-2">
        <thead className="bg-gray-100 text-gray-600 uppercase text-xs">
          <tr>
            {headers.map((header, index) => (
              <th key={index} className="px-4 py-2 border-r border-gray-200">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {data.length === 0 ? (
            <tr>
              <td colSpan={headers.length} className="px-4 py-4 text-center text-gray-500">
                {noDataMessage}
              </td>
            </tr>
          ) : (
            data.map((item, index) => renderRow(item, index))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default ReusableTable;