import React, { memo } from 'react';
import Chart from 'react-apexcharts';

const RadialGauge = memo(({ value, color, label }) => {
  const options = {
    chart: { 
      type: 'radialBar',
      animations: { enabled: true, easing: 'easeinout', speed: 800 }
    },
    plotOptions: {
      radialBar: {
        startAngle: -135,
        endAngle: 135,
        hollow: { size: '70%' },
        track: { background: '#1e222d', strokeWidth: '100%' },
        dataLabels: {
          name: { show: true, color: '#64748b', fontSize: '10px', fontWeight: 600, offsetY: 40 },
          value: { 
            offsetY: -5, 
            fontSize: '20px', 
            color: '#fff', 
            fontWeight: 700, 
            formatter: (v) => v + '%' 
          }
        }
      }
    },
    fill: { colors: [color] },
    stroke: { lineCap: 'round' },
    labels: [label.toUpperCase()]
  };

  return (
    <div className="gauge-container w-full">
      <Chart options={options} series={[value || 0]} type="radialBar" height={220} />
    </div>
  );
});

export default RadialGauge;