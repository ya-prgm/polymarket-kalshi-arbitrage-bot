
import React, { useState, useEffect, useRef, memo, useMemo } from 'react';
import Chart from 'react-apexcharts';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, Terminal, ShieldCheck, ExternalLink, Cpu, Wallet, 
  Play, RefreshCw, Settings, Database, Search, ChevronDown, 
  BarChart3, ShieldAlert, ArrowDown, ArrowUp, 
  Clock, Calendar, TrendingUp, Layers, Activity, Globe, HardDrive,
  ArrowUpDown, Download, Radio, History, ArrowLeft, FileText,
  SlidersHorizontal, X
} from 'lucide-react';


const useSmoothProgress = (targetValue, duration = 1500) => {
  const [value, setValue] = useState(targetValue);
  
  useEffect(() => {
    let startValue = value;
    let startTime = performance.now();
    let frameId;
    
    const animate = (currentTime) => {
      let elapsed = currentTime - startTime;
      let progress = elapsed / duration;
      if (progress > 1) progress = 1;
      
      // Эффект замедления к концу (Ease Out Cubic)
      const easeOut = 1 - Math.pow(1 - progress, 3);
      setValue(startValue + (targetValue - startValue) * easeOut);
      
      if (progress < 1) {
        frameId = requestAnimationFrame(animate);
      }
    };
    
    frameId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameId);
  }, [targetValue]);
  
  return value;
};

// =============================================================================
// --- ГРАФИКИ ---
// =============================================================================

const RadialGauge = memo(({ value, color, label }) => {
  const options = {
    chart: { 
      type: 'radialBar', 
      sparkline: { enabled: true },
      animations: { enabled: true, speed: 800, dynamicAnimation: { enabled: true, speed: 800 } }
    },
    plotOptions: {
      radialBar: {
        startAngle: -110,
        endAngle: 110,
        hollow: { size: '65%', background: 'transparent' },
        track: { background: '#1e263c', strokeWidth: '100%', margin: 5 },
        dataLabels: {
          name: { show: true, color: '#676d7d', fontSize: '10px', offsetY: 45, fontWeight: 800 },
          value: { 
            offsetY: -5, fontSize: '26px', color: '#fff', fontWeight: 900, 
            fontFamily: 'JetBrains Mono', formatter: (v) => Math.round(v) + '%' 
          }
        }
      }
    },
    fill: { type: 'gradient', gradient: { shade: 'dark', type: 'horizontal', gradientToColors: [color], stops: [0, 100] } },
    stroke: { lineCap: 'round' },
    colors: [color],
    labels: [label.toUpperCase()]
  };

  return (
    <div className="chart-wrapper w-[180px]">
      <Chart options={options} series={[value || 0]} type="radialBar" height={260} />
    </div>
  );
});

// =============================================================================
// --- ОСНОВНОЕ ПРИЛОЖЕНИЕ ---
// =============================================================================

const App = () => {

  const [currentView, setCurrentView] = useState('main'); // 'main', 'history', 'history_detail'


  const [scanId, setScanId] = useState(null);
  const [status, setStatus] = useState('IDLE');
  const [progress, setProgress] = useState(0);
  const smoothProgress = useSmoothProgress(progress, 1500); 
  
  const [deals, setDeals] = useState([]);
  const [logs, setLogs] = useState(">>> SYSTEM READY...\n>>> WAITING FOR COMMAND...");
  

  const [historyList, setHistoryList] = useState([]);
  const [historyDeals, setHistoryDeals] = useState([]);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);


  const [sysStats, setSysStats] = useState({ cpu: 0, ram: 0, disk: 0, ds_balance: "0.00 USD" });
  const smoothedStatsRef = useRef({ cpu: null, ram: null, disk: null }); 
  
  const [globalStats, setGlobalStats] = useState({ total_deals_in_db: 0, total_scans_performed: 0 });
  const [searchTerm, setSearchTerm] = useState("");
  const [sortConfig, setSortConfig] = useState({ key: 'profit', direction: 'desc' });
  const [openCat, setOpenCat] = useState('finance');
  
  const consoleRef = useRef(null);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [isReparsing, setIsReparsing] = useState(false);

  const [showFilters, setShowFilters] = useState(false);
  const [localFilters, setLocalFilters] = useState({
    minProfit: "0.01",
    maxProfit: "100.0",
    minPrice: "0.10",
    maxPrice: "0.90",
    active: false
  });

  const [config, setConfig] = useState({
    TOTAL_LIMIT: "5000", 
    BANKROLL: "1000",
    DEEPSEEK_KEY: "sk-a1e7ff85f219420593f3a65767ecd216", 
    AI_THRESHOLD: "0.63",
    POLY_SORT_BY: "volume24hr", 
    KALSHI_SORT_BY: "trending", 
    DEBUG_MODE: "false"
  });


  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [logs]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/settings')
      .then(r => r.json())
      .then(d => setConfig(prev => ({...prev, ...d})))
      .catch(() => {});
      
    // Загружаем последнюю таблицу
    fetch('http://127.0.0.1:8000/api/scan/latest')
      .then(r => r.json())
      .then(data => {
        if (data && data.deals && data.deals.length > 0) {
          setDeals(data.deals);
          setScanId(data.scan_id);
          setStatus('COMPLETED');
          setProgress(100);
          setLogs(`>>> LOADED LATEST SCAN SESSION: ${data.scan_id}\n>>> FOUND ${data.deals.length} DEALS.`);
        }
      }).catch(() => {});
      
    const statsTimer = setInterval(() => {
      fetch('http://127.0.0.1:8000/api/stats/global').then(r => r.json()).then(d => setGlobalStats(d)).catch(()=>{}); 
      fetch('http://127.0.0.1:8000/api/deepseek/balance').then(r => r.json()).then(b => setSysStats(prev => ({ ...prev, ds_balance: b.total || "0.00" }))).catch(()=>{}); 
      
      // Плавное вычисление нагрузки (Экспоненциальное скользящее среднее)
      fetch('http://127.0.0.1:8000/api/system/stats').then(r => r.json()).then(s => {
        const alpha = 0.2; // Коэффициент сглаживания (20% новые данные, 80% старые)
        const prev = smoothedStatsRef.current;
        
        const newCpu = prev.cpu === null ? s.cpu : (s.cpu * alpha) + (prev.cpu * (1 - alpha));
        const newRam = prev.ram === null ? s.ram : (s.ram * alpha) + (prev.ram * (1 - alpha));
        const newDisk = prev.disk === null ? s.disk : (s.disk * alpha) + (prev.disk * (1 - alpha));
        
        smoothedStatsRef.current = { cpu: newCpu, ram: newRam, disk: newDisk };
        
        setSysStats(prevStats => ({ 
          ...prevStats, 
          cpu: newCpu, 
          ram: newRam, 
          disk: newDisk 
        }));
      }).catch(()=>{});
    }, 2000);
    
    return () => clearInterval(statsTimer);
  }, []);


  const loadHistoryList = async () => {
    setCurrentView('history');
    try {
      const res = await fetch('http://127.0.0.1:8000/api/history');
      const data = await res.json();
      setHistoryList(data);
    } catch (e) { console.error("Failed to load history", e); }
  };

  const viewHistoryDetail = async (id) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/scan/results/${id}`);
      const data = await res.json();
      setHistoryDeals(data);
      setSelectedHistoryId(id);
      setCurrentView('history_detail');
    } catch (e) { console.error("Failed to load history details", e); }
  };

  const exportToTxt = (dealsToExport) => {
    if (!dealsToExport || dealsToExport.length === 0) return;
    
    let text = "=========================================\n";
    text += "      ARBITRAGE SCANNER PRO - EXPORT     \n";
    text += "=========================================\n";
    text += `Date: ${new Date().toLocaleString()}\n`;
    text += `Total Deals: ${dealsToExport.length}\n\n`;

    dealsToExport.forEach((d, i) => {
      text += `[${i + 1}] PROFIT: ${d.arbitrage?.profit_percent}%\n`;
      text += `-----------------------------------------\n`;
      text += `POLYMARKET: ${d.poly?.question}\n`;
      text += `  -> Target: ${d.arbitrage?.poly_side} | Price: ${d.arbitrage?.poly_price_pct}%\n`;
      text += `  -> Stake: $${d.arbitrage?.poly_stake_money}\n`;
      text += `  -> Link: ${d.poly?.url}\n\n`;
      
      text += `KALSHI: ${d.kalshi?.question}\n`;
      text += `  -> Target: ${d.arbitrage?.kalshi_side} | Price: ${d.arbitrage?.kalshi_price_pct}%\n`;
      text += `  -> Stake: $${d.arbitrage?.kalshi_stake_money}\n`;
      text += `  -> Link: ${d.kalshi?.url}\n\n`;
      
      text += `AI Match Score: ${Math.round(d.similarity * 100)}%\n`;
      text += `Days Remaining: ${d.arbitrage?.days_remaining}\n`;
      text += `=========================================\n\n`;
    });

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `arbitrage_export_${new Date().getTime()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };


  const handleReparse = async () => {
    if (deals.length === 0 || isReparsing) return;
    setIsReparsing(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/reparse', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(deals)
      });
      if (res.ok) {
        const updatedDeals = await res.json();
        if (updatedDeals && updatedDeals.length > 0) setDeals(updatedDeals);
      }
    } catch (e) { console.error(e); } finally { setTimeout(() => setIsReparsing(false), 600); }
  };

  useEffect(() => {
    let interval;
    if (isLiveMode && deals.length > 0 && currentView === 'main') {
      interval = setInterval(() => handleReparse(), 60000);
    }
    return () => clearInterval(interval);
  }, [isLiveMode, deals.length, currentView]);

  useEffect(() => {
    let poll;
    if (scanId && status !== 'COMPLETED' && !status.includes('FAILED') && currentView === 'main') {
      poll = setInterval(async () => {
        try {
          const sRes = await fetch(`http://127.0.0.1:8000/api/scan/status/${scanId}`).then(r => r.json());
          setProgress(sRes.progress);
          setStatus(sRes.status.toUpperCase());
          const lRes = await fetch(`http://127.0.0.1:8000/api/scan/log/${scanId}`).then(r => r.text());
          setLogs(lRes);
          if (sRes.status === 'completed') {
            clearInterval(poll);
            const dRes = await fetch(`http://127.0.0.1:8000/api/scan/results/${scanId}`).then(r => r.json());
            setDeals(dRes);
          }
        } catch (e) {}
      }, 1500);
    }
    return () => clearInterval(poll);
  }, [scanId, status, currentView]);

  const handleStart = async () => {
    setDeals([]); 
    setLogs(">>> INITIALIZING NEURAL BRIDGE...\n>>> SYNCING CONFIGURATION WITH BACKEND..."); 
    setProgress(0); 
    setStatus('STARTING');
    
    try {
      await fetch('http://127.0.0.1:8000/api/settings', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(config)
      });
      const res = await fetch('http://127.0.0.1:8000/api/scan/start', { method: 'POST' });
      const data = await res.json();
      setScanId(data.scan_id);
    } catch (e) { 
      setStatus('FAILED'); 
      setLogs(prev => prev + "\n[!] CRITICAL ERROR: Failed to connect to backend API.");
    }
  };

  const processedDeals = useMemo(() => {
    let source = currentView === 'main' ? deals : historyDeals;

    if (searchTerm) {
      const l = searchTerm.toLowerCase();
      source = source.filter(d => d.poly?.question?.toLowerCase().includes(l) || d.kalshi?.question?.toLowerCase().includes(l));
    }

    source.sort((a, b) => {
      let vA = a.arbitrage?.[sortConfig.key === 'profit' ? 'profit_percent' : sortConfig.key === 'days' ? 'days_remaining' : ''] || 0;
      let vB = b.arbitrage?.[sortConfig.key === 'profit' ? 'profit_percent' : sortConfig.key === 'days' ? 'days_remaining' : ''] || 0;
      if (sortConfig.key === 'ai') { vA = a.similarity; vB = b.similarity; }
      return sortConfig.direction === 'desc' ? vB - vA : vA - vB;
    });

    let matched = [];
    let others = [];

    if (localFilters.active) {
      const minProf = localFilters.minProfit !== "" ? parseFloat(localFilters.minProfit) : -Infinity;
      const maxProf = localFilters.maxProfit !== "" ? parseFloat(localFilters.maxProfit) : Infinity;
      const minPrc = localFilters.minPrice !== "" ? parseFloat(localFilters.minPrice) : 0;
      const maxPrc = localFilters.maxPrice !== "" ? parseFloat(localFilters.maxPrice) : 1;

      source.forEach(d => {
        const prof = d.arbitrage?.profit_percent || 0;
        const pPrice = (d.arbitrage?.poly_price_pct || 0) / 100;
        const kPrice = (d.arbitrage?.kalshi_price_pct || 0) / 100;

        const passProfit = (isNaN(minProf) || prof >= minProf) && (isNaN(maxProf) || prof <= maxProf);
        const passPrice = (isNaN(minPrc) || (pPrice >= minPrc && kPrice >= minPrc)) &&
                          (isNaN(maxPrc) || (pPrice <= maxPrc && kPrice <= maxPrc));

        if (passProfit && passPrice) {
          matched.push(d);
        } else {
          others.push(d);
        }
      });
    } else {
      matched = source;
    }

    return { matched, others };
  }, [deals, historyDeals, currentView, searchTerm, sortConfig, localFilters]);

  // --- РЕНДЕР СТРОКИ ТАБЛИЦЫ ---
  const renderDealRow = (deal, idx, isOther = false) => (
    <tr key={`${deal.poly?.question}-${idx}`} className={`row-hover-effect group ${isOther ? 'opacity-40 hover:opacity-100 grayscale hover:grayscale-0 transition-all duration-500' : ''}`}>
      <td className="px-12 py-12">
        <div className="flex flex-col relative">
          <AnimatePresence mode="wait">
            <motion.span 
              key={deal.arbitrage?.profit_percent}
              initial={{ opacity: 0.5, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className={`text-6xl font-data-mono font-black tracking-tighter ${deal.arbitrage?.profit_percent > 0 ? 'text-success neon-text-success' : 'text-danger'}`}
            >
              {deal.arbitrage?.profit_percent}%
            </motion.span>
          </AnimatePresence>
          <div className="flex items-center gap-2 mt-3">
            <TrendingUp size={16} className={deal.arbitrage?.profit_percent > 0 ? 'text-success' : 'text-danger'} />
            <span className="text-[10px] font-header-heavy text-gray-500 tracking-widest uppercase">Yield</span>
            {deal.is_live && <span className="ml-2 text-[9px] bg-success/20 text-success px-2 py-0.5 rounded-md font-black animate-pulse">LIVE {deal.last_update}</span>}
          </div>
        </div>
      </td>
      <td className="px-8 py-12 max-w-2xl">
        <div className="space-y-10">
          <div className="relative pl-8 border-l-4 border-info">
            <p className="text-[10px] font-header-heavy text-info mb-2 tracking-widest uppercase">POLYMARKET</p>
            <p className="text-xl font-bold text-white leading-tight tracking-tight group-hover:text-info transition-colors">{deal.poly?.question}</p>
            <div className="mt-4 flex gap-8 text-[11px] font-header-heavy uppercase">
               <span>Target: <span className={deal.arbitrage?.poly_side === 'Yes' ? 'text-success' : 'text-danger'}>{deal.arbitrage?.poly_side}</span></span>
               <span>Price: <span className="text-white font-data-mono">{deal.arbitrage?.poly_price_pct}%</span></span>
            </div>
          </div>
          <div className="relative pl-8 border-l-4 border-warning">
            <p className="text-[10px] font-header-heavy text-warning mb-2 tracking-widest uppercase">KALSHI</p>
            <p className="text-xl font-bold text-gray-400 leading-tight tracking-tight group-hover:text-warning transition-colors">{deal.kalshi?.question}</p>
            <div className="mt-4 flex gap-8 text-[11px] font-header-heavy uppercase">
               <span>Target: <span className={deal.arbitrage?.kalshi_side === 'Yes' ? 'text-success' : 'text-danger'}>{deal.arbitrage?.kalshi_side}</span></span>
               <span>Price: <span className="text-white font-data-mono">{deal.arbitrage?.kalshi_price_pct}%</span></span>
            </div>
          </div>
        </div>
      </td>
      <td className="px-8 py-12">
        <div className="flex flex-col gap-6">
           <div className="bg-black/40 p-6 rounded-[1.5rem] border border-white/5 shadow-2xl">
              <div className="text-[10px] font-header-heavy text-gray-500 tracking-widest mb-3 uppercase">Poly Stake</div>
              <div className="text-2xl font-data-mono font-black text-white">${deal.arbitrage?.poly_stake_money}</div>
           </div>
           <div className="bg-black/40 p-6 rounded-[1.5rem] border border-white/5 shadow-2xl">
              <div className="text-[10px] font-header-heavy text-gray-500 tracking-widest mb-3 uppercase">Kalshi Stake</div>
              <div className="text-2xl font-data-mono font-black text-white">${deal.arbitrage?.kalshi_stake_money}</div>
           </div>
        </div>
      </td>
      <td className="px-8 py-12">
        <div className="flex flex-col items-start gap-4">
           <div className="flex items-center gap-4 bg-white/5 px-6 py-3 rounded-2xl border border-white/5 shadow-xl">
              <Clock size={24} className="text-primary" /><span className="text-3xl font-data-mono font-black text-white">{deal.arbitrage?.days_remaining}D</span>
           </div>
           <div className="flex flex-col gap-1 ml-2"><span className="text-[10px] font-header-heavy text-gray-600 uppercase tracking-widest">Resolution:</span><span className="text-sm font-data-mono font-black text-gray-400">{deal.arbitrage?.market_dates?.final_close_date}</span></div>
        </div>
      </td>
      <td className="px-8 py-12 text-center">
        <div className="inline-flex flex-col items-center p-8 bg-primary/5 rounded-[2.5rem] border border-primary/10 min-w-[140px] shadow-2xl group-hover:border-primary/40 transition-all">
          <ShieldCheck size={40} className="text-primary" /><span className="text-3xl font-data-mono font-black mt-4 text-white">{Math.round(deal.similarity * 100)}%</span>
          <span className="text-[9px] font-header-heavy text-gray-500 uppercase tracking-widest mt-2">Match Score</span>
        </div>
      </td>
      <td className="px-12 py-12 text-right">
        <div className="flex flex-col gap-4 items-end">
          <a href={deal.poly?.url} target="_blank" rel="noreferrer" className="flex items-center gap-3 px-8 py-4 bg-info/10 text-info rounded-2xl text-[11px] font-header-heavy uppercase hover:bg-info/20 transition-all border border-info/20 w-48 justify-center shadow-lg">Polymarket <ExternalLink size={16} /></a>
          <a href={deal.kalshi?.url} target="_blank" rel="noreferrer" className="flex items-center gap-3 px-8 py-4 bg-warning/10 text-warning rounded-2xl text-[11px] font-header-heavy uppercase hover:bg-warning/20 transition-all border border-warning/20 w-48 justify-center shadow-lg">Kalshi <ExternalLink size={16} /></a>
          <button className="w-48 py-4 bg-primary text-white rounded-2xl text-[11px] font-header-heavy uppercase shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all">Execute Trade</button>
        </div>
      </td>
    </tr>
  );

  return (
    <div className="min-h-screen bg-[#0b0e19] text-[#d0d2d6] p-6 lg:p-10 relative overflow-x-hidden">
      {/* BACKGROUND DECOR */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[60%] h-[60%] bg-primary/10 blur-[180px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[60%] bg-info/10 blur-[180px] rounded-full" />
      </div>

      {/* NAVIGATION TABS */}
      <div className="flex gap-4 mb-8 relative z-10">
        <button 
          onClick={() => setCurrentView('main')} 
          className={`px-6 py-3 rounded-xl font-bold flex items-center gap-3 transition-all ${currentView === 'main' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
        >
          <Activity size={18}/> Main Dashboard
        </button>
        <button 
          onClick={loadHistoryList} 
          className={`px-6 py-3 rounded-xl font-bold flex items-center gap-3 transition-all ${currentView === 'history' || currentView === 'history_detail' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'bg-white/5 text-gray-400 hover:bg-white/10'}`}
        >
          <History size={18}/> Scan History
        </button>
      </div>

      {/* ========================================================= */}
      {/* MAIN DASHBOARD VIEW */}
      {/* ========================================================= */}
      {currentView === 'main' && (
        <>
          {/* TOP STATS */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-10 relative z-10">
            <StatCard label="DEEPSEEK BALANCE" value={sysStats.ds_balance} icon={<Wallet size={32}/>} color="warning" sub="Neural Credits" />
            <StatCard label="DATABASE PAIRS" value={globalStats.total_deals_in_db} icon={<Database size={32}/>} color="primary" sub="Total Scanned" />
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="lg:col-span-3 glass-panel rounded-[2.5rem] p-6 flex items-center justify-around relative overflow-hidden h-[240px]">
              <RadialGauge value={sysStats.cpu} color="#7367f0" label="CPU Engine" />
              <RadialGauge value={sysStats.ram} color="#ea5455" label="Memory" />
              <RadialGauge value={sysStats.disk} color="#00cfe8" label="Storage" />
              <div className="hidden xl:flex flex-col gap-4 border-l border-white/10 pl-10">
                 <div className="flex items-center gap-3 text-xs font-semibold text-success"><div className="w-2.5 h-2.5 rounded-full bg-success animate-pulse" /> SYSTEM ONLINE</div>
                 <div className="flex items-center gap-3 text-xs font-semibold text-gray-500"><Layers size={18}/> WORKERS: 12</div>
                 <div className="flex items-center gap-3 text-xs font-semibold text-primary"><Zap size={18} fill="currentColor"/> developed by by prgm</div>
              </div>
            </motion.div>
          </div>

          {/* MIDDLE ROW */}
          <div className="grid grid-cols-12 gap-8 mb-10 relative z-10">
            <div className="col-span-12 xl:col-span-4 flex flex-col">
              <motion.div initial={{ x: -50, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="glass-panel rounded-[2.5rem] p-10 flex-grow flex flex-col">
                <div className="flex items-center gap-5 mb-10">
                   <div className="w-14 h-14 bg-primary/10 rounded-2xl flex items-center justify-center text-primary shadow-2xl shadow-primary/20"><Settings className="animate-spin-slow" size={28} /></div>
                   <h2 className="text-3xl font-bold text-white tracking-tight">Control</h2>
                </div>
                <div className="space-y-5 flex-grow overflow-y-auto no-scrollbar pr-2">
                  <CategoryItem title="FINANCE & LIMITS" icon={<Wallet size={18}/>} isOpen={openCat === 'finance'} onClick={() => setOpenCat('finance')}>
                    <ConfigInput label="DEEPSEEK API KEY" type="password" value={config.DEEPSEEK_KEY} onChange={v => setConfig({...config, DEEPSEEK_KEY: v})} />
                    <div className="grid grid-cols-2 gap-4">
                      <ConfigInput label="BANKROLL ($)" value={config.BANKROLL} onChange={v => setConfig({...config, BANKROLL: v})} />
                      <ConfigInput label="TOTAL LIMIT" value={config.TOTAL_LIMIT} onChange={v => setConfig({...config, TOTAL_LIMIT: v})} />
                    </div>
                    <Select label="DEBUG MODE (SAVE JSONS)" value={config.DEBUG_MODE} options={['true', 'false']} onChange={v => setConfig({...config, DEBUG_MODE: v})} />
                  </CategoryItem>
                  <CategoryItem title="NEURAL PARAMETERS" icon={<ShieldAlert size={18}/>} isOpen={openCat === 'ai'} onClick={() => setOpenCat('ai')}>
                    <ConfigInput label="AI CONFIDENCE THRESHOLD" value={config.AI_THRESHOLD} onChange={v => setConfig({...config, AI_THRESHOLD: v})} />
                  </CategoryItem>
                  <CategoryItem title="EXCHANGE SORTING" icon={<BarChart3 size={18}/>} isOpen={openCat === 'exchange'} onClick={() => setOpenCat('exchange')}>
                    <Select label="Poly Sort By" value={config.POLY_SORT_BY} options={['volume24hr', 'endDate', 'false']} onChange={v => setConfig({...config, POLY_SORT_BY: v})} />
                    <Select label="Kalshi Sort By" value={config.KALSHI_SORT_BY} options={['trending', 'closing', 'false']} onChange={v => setConfig({...config, KALSHI_SORT_BY: v})} />
                  </CategoryItem>
                </div>
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={handleStart} disabled={status !== 'IDLE' && status !== 'COMPLETED'} className="w-full py-6 rounded-2xl font-bold text-lg bg-primary text-white shadow-2xl flex items-center justify-center gap-4 disabled:opacity-50 mt-8 tracking-widest">
                  {status === 'STARTING' ? <RefreshCw className="animate-spin" size={24} /> : <Play fill="currentColor" size={24} />} ENABLE NEURAL SCANNER
                </motion.button>
              </motion.div>
            </div>

            <div className="col-span-12 xl:col-span-8 flex flex-col">
              <motion.div initial={{ x: 50, opacity: 0 }} animate={{ x: 0, opacity: 1 }} className="glass-panel rounded-[2.5rem] p-10 flex-grow flex flex-col">
                <div className="flex justify-between items-end mb-8">
                  <div><h2 className="text-3xl font-bold text-white tracking-tight">Status: <span className="text-primary neon-text-primary font-data-mono">{status}</span></h2><p className="text-xs font-semibold text-gray-400 tracking-[0.4em] mt-1 animate-pulse">NEURAL DATA STREAM ACTIVE</p></div>
                  <span className="text-5xl font-data-mono font-black text-white leading-none">{Math.round(smoothProgress)}%</span>
                </div>
                <div className="w-full bg-black/40 h-4 rounded-full overflow-hidden p-1 border border-white/5 mb-8">
                  <motion.div style={{ width: `${smoothProgress}%` }} className="h-full bg-gradient-to-r from-primary to-info rounded-full shadow-[0_0_25px_#7367f0]" />
                </div>
                {/* КОНСОЛЬ С ИСПРАВЛЕННЫМ СКРОЛЛОМ */}
                <div 
                  ref={consoleRef}
                  className="flex-grow bg-black/40 rounded-[2rem] p-8 font-data-mono text-[13px] text-success/90 border border-white/5 relative overflow-y-auto custom-scroll shadow-2xl min-h-[350px]"
                >
                  {logs.split('\n').map((line, i) => {
                    let lineClass = "py-1 border-l-2 border-transparent hover:border-primary hover:bg-white/5 pl-4 transition-all whitespace-pre-wrap";
                    if (line.includes("❌") || line.includes("[!]")) lineClass += " text-danger";
                    if (line.includes("✅") || line.includes("🔥")) lineClass += " text-primary font-bold";
                    if (line.includes("⚠️")) lineClass += " text-warning";
                    return <div key={i} className={lineClass}>{line}</div>;
                  })}
                </div>
              </motion.div>
            </div>
          </div>
        </>
      )}

      {/* ========================================================= */}
      {/* HISTORY LIST VIEW */}
      {/* ========================================================= */}
      {currentView === 'history' && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="relative z-10 w-full min-h-[600px]">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center text-primary"><History size={24} /></div>
            <h2 className="text-3xl font-bold text-white tracking-tight">Scan History</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {historyList.length > 0 ? historyList.map((scan) => (
              <motion.div 
                key={scan.id}
                whileHover={{ y: -5 }}
                onClick={() => viewHistoryDetail(scan.id)}
                className="glass-panel p-8 rounded-[2rem] cursor-pointer hover:border-primary/40 transition-all group relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-full -z-10 group-hover:bg-primary/10 transition-colors" />
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <p className="text-[10px] font-header-heavy text-gray-500 uppercase tracking-widest mb-1">Session ID</p>
                    <p className="text-xl font-data-mono font-bold text-white">{scan.id}</p>
                  </div>
                  <div className="bg-success/10 text-success px-3 py-1 rounded-lg text-xs font-bold border border-success/20">COMPLETED</div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-center justify-between bg-black/40 p-4 rounded-xl border border-white/5">
                    <div className="flex items-center gap-3 text-gray-400"><Calendar size={16}/> <span className="text-sm font-bold">Date</span></div>
                    <span className="text-sm font-data-mono text-white">{new Date(scan.end_time).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between bg-black/40 p-4 rounded-xl border border-white/5">
                    <div className="flex items-center gap-3 text-gray-400"><Activity size={16}/> <span className="text-sm font-bold">Deals Found</span></div>
                    <span className="text-lg font-data-mono font-black text-primary">{scan.total_deals}</span>
                  </div>
                </div>
              </motion.div>
            )) : (
              <div className="col-span-full py-20 text-center opacity-50">
                <Database size={64} className="mx-auto mb-4 text-gray-500" />
                <p className="text-xl font-bold">No history records found.</p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* ========================================================= */}
      {/* TABLE SECTION (SHARED FOR MAIN AND HISTORY DETAIL) */}
      {/* ========================================================= */}
      {(currentView === 'main' || currentView === 'history_detail') && (
        <motion.div initial={{ y: 100, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="glass-panel rounded-[3rem] overflow-hidden relative z-10 w-full min-h-[900px]">
          <div className="p-12 border-b border-white/5 flex flex-col lg:flex-row justify-between items-center gap-10 bg-white/[0.02]">
            
            {/* TABLE HEADER LEFT */}
            <div>
              {currentView === 'history_detail' ? (
                <div className="flex items-center gap-6">
                  <button onClick={() => setCurrentView('history')} className="w-12 h-12 bg-white/5 hover:bg-white/10 rounded-full flex items-center justify-center transition-colors border border-white/10">
                    <ArrowLeft size={24} />
                  </button>
                  <div>
                    <h2 className="text-4xl font-header-heavy text-white italic tracking-tighter">Session: {selectedHistoryId}</h2>
                    <p className="text-xs font-header-heavy text-gray-500 tracking-[0.3em] mt-2">HISTORICAL DATA ARCHIVE</p>
                  </div>
                </div>
              ) : (
                <>
                  <h2 className="text-4xl font-header-heavy text-white italic tracking-tighter">Arbitrage Signals</h2>
                  <div className="flex items-center gap-4 mt-2">
                     <p className="text-xs font-header-heavy text-gray-500 tracking-[0.3em]">LIVE MARKET INEFFICIENCIES DETECTED</p>
                     {isLiveMode && <div className="flex items-center gap-2 px-3 py-1 bg-success/10 rounded-full border border-success/20"><div className="w-1.5 h-1.5 bg-success rounded-full animate-pulse"/><span className="text-[9px] font-black text-success uppercase tracking-widest">Live Monitoring</span></div>}
                  </div>
                </>
              )}
            </div>
            
            {/* TABLE HEADER RIGHT (CONTROLS) */}
            <div className="flex items-center gap-6 w-full lg:w-auto">
              
              {/* Показывать Live Controls только на главной */}
              {currentView === 'main' && (
                <>
                  <div className="flex items-center gap-4 bg-black/40 p-2 rounded-2xl border border-white/5 pr-6">
                     <button 
                      onClick={() => setIsLiveMode(!isLiveMode)}
                      className={`w-14 h-8 rounded-xl relative transition-all ${isLiveMode ? 'bg-success shadow-[0_0_15px_rgba(40,199,111,0.4)]' : 'bg-white/10'}`}
                     >
                       <motion.div animate={{ x: isLiveMode ? 28 : 4 }} className="absolute top-1 w-6 h-6 bg-white rounded-lg shadow-lg" />
                     </button>
                     <span className="text-[10px] font-black text-white uppercase tracking-widest">Auto-Update</span>
                  </div>

                  <button 
                    onClick={handleReparse}
                    disabled={isReparsing || deals.length === 0}
                    className={`p-5 rounded-2xl border transition-all flex items-center justify-center
                      ${isReparsing 
                        ? 'bg-primary/20 border-primary/40 text-primary cursor-wait' 
                        : 'bg-primary/10 border-primary/20 text-primary hover:bg-primary/20 active:scale-90'
                      } ${deals.length === 0 ? 'opacity-20 grayscale' : 'opacity-100'}`}
                  >
                    <RefreshCw size={24} className={isReparsing ? 'animate-spin' : ''} />
                  </button>
                </>
              )}

              {/* Кнопка экспорта в TXT */}
              <button 
                onClick={() => exportToTxt(processedDeals.matched)}
                className="p-5 rounded-2xl border bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:text-white transition-all flex items-center justify-center group"
                title="Export to TXT"
              >
                <Download size={24} className="group-hover:scale-110 transition-transform" />
              </button>

              {/* КНОПКА ФИЛЬТРОВ (REAL-TIME) */}
              <div className="relative">
                <button 
                  onClick={() => setShowFilters(!showFilters)}
                  className={`p-5 rounded-2xl border transition-all flex items-center justify-center gap-3 font-bold text-sm
                    ${localFilters.active ? 'bg-primary text-white border-primary shadow-[0_0_15px_rgba(115,103,240,0.4)]' : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:text-white'}`}
                >
                  <SlidersHorizontal size={20} /> FILTERS
                  {localFilters.active && <div className="w-2 h-2 rounded-full bg-white animate-pulse" />}
                </button>

                <AnimatePresence>
                  {showFilters && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute top-full right-0 mt-4 w-80 bg-[#111526] border border-white/10 rounded-3xl p-6 shadow-2xl z-50 backdrop-blur-xl"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-bold text-white tracking-widest uppercase flex items-center gap-2"><BarChart3 size={16} className="text-primary"/> Real-time Filters</h3>
                        <button onClick={() => setShowFilters(false)} className="text-gray-500 hover:text-white"><X size={18}/></button>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <ConfigInput label="MIN PROFIT %" value={localFilters.minProfit} onChange={v => setLocalFilters({...localFilters, minProfit: v})} />
                          <ConfigInput label="MAX PROFIT %" value={localFilters.maxProfit} onChange={v => setLocalFilters({...localFilters, maxProfit: v})} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <ConfigInput label="MIN PRICE" value={localFilters.minPrice} onChange={v => setLocalFilters({...localFilters, minPrice: v})} />
                          <ConfigInput label="MAX PRICE" value={localFilters.maxPrice} onChange={v => setLocalFilters({...localFilters, maxPrice: v})} />
                        </div>
                        
                        <div className="pt-4 flex gap-3 border-t border-white/5 mt-2">
                          <button 
                            onClick={() => setLocalFilters({...localFilters, active: !localFilters.active})}
                            className={`flex-1 py-3 rounded-xl font-bold text-xs tracking-widest uppercase transition-all ${localFilters.active ? 'bg-danger/20 text-danger hover:bg-danger/30' : 'bg-primary text-white shadow-lg shadow-primary/30 hover:scale-105'}`}
                          >
                            {localFilters.active ? 'Disable Filters' : 'Apply Filters'}
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="relative group w-full lg:w-80">
                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-primary transition-colors" size={22} />
                <input 
                  type="text" placeholder="FILTER SIGNALS..." 
                  className="bg-black/40 border border-white/10 rounded-2xl py-5 pl-16 pr-8 text-sm outline-none focus:border-primary w-full transition-all font-bold shadow-inner"
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-white/[0.03] text-[11px] font-header-heavy text-gray-500 tracking-widest">
                  <th className="px-12 py-8 cursor-pointer hover:text-white" onClick={() => setSortConfig({key:'profit', direction: sortConfig.direction === 'desc' ? 'asc' : 'desc'})}>
                    <div className="flex items-center gap-3">PROFIT {sortConfig.key === 'profit' && (sortConfig.direction === 'desc' ? <ArrowDown size={14}/> : <ArrowUp size={14}/>)}</div>
                  </th>
                  <th className="px-8 py-8">MARKET COMPARISON (POLY VS KALSHI)</th>
                  <th className="px-8 py-8">STRATEGY & STAKES</th>
                  <th className="px-8 py-8 cursor-pointer hover:text-white" onClick={() => setSortConfig({key:'days', direction: sortConfig.direction === 'desc' ? 'asc' : 'desc'})}>
                    <div className="flex items-center gap-3">TIMELINE {sortConfig.key === 'days' && <ArrowDown size={14}/>}</div>
                  </th>
                  <th className="px-8 py-8 text-center cursor-pointer hover:text-white" onClick={() => setSortConfig({key:'ai', direction: sortConfig.direction === 'desc' ? 'asc' : 'desc'})}>
                    <div className="flex items-center justify-center gap-3">AI SCORE {sortConfig.key === 'ai' && <ArrowDown size={14}/>}</div>
                  </th>
                  <th className="px-12 py-8 text-right">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                
                {/* РЕНДЕР ОТФИЛЬТРОВАННЫХ (MATCHED) СДЕЛОК */}
                {processedDeals.matched.length > 0 ? (
                  processedDeals.matched.map((deal, idx) => renderDealRow(deal, idx, false))
                ) : (
                  <tr>
                    <td colSpan="6" className="py-40 text-center opacity-20">
                      <Activity size={80} className="text-gray-500 animate-pulse mb-6 mx-auto" />
                      <p className="text-2xl font-header-heavy text-gray-500 italic">Awaiting Neural Signals...</p>
                    </td>
                  </tr>
                )}

                {/* РАЗДЕЛИТЕЛЬ И РЕНДЕР ОСТАЛЬНЫХ (OTHERS) СДЕЛОК */}
                {localFilters.active && processedDeals.others.length > 0 && (
                  <>
                    <tr>
                      <td colSpan="6" className="py-12 bg-black/20">
                        <div className="flex items-center justify-center gap-6 opacity-60">
                          <div className="h-px bg-gradient-to-r from-transparent to-white/30 flex-grow max-w-md"></div>
                          <span className="text-xs font-header-heavy tracking-[0.4em] uppercase text-gray-400 flex items-center gap-3">
                            <SlidersHorizontal size={14} /> Unfiltered / Others
                          </span>
                          <div className="h-px bg-gradient-to-l from-transparent to-white/30 flex-grow max-w-md"></div>
                        </div>
                      </td>
                    </tr>
                    {processedDeals.others.map((deal, idx) => renderDealRow(deal, idx, true))}
                  </>
                )}

              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
};

// --- HELPER COMPONENTS ---

const StatCard = ({ label, value, icon, color, sub }) => {
  const colors = { primary: "text-primary shadow-primary/10", warning: "text-warning shadow-warning/10" };
  return (
    <motion.div whileHover={{ y: -5 }} className="glass-panel p-8 rounded-[2.5rem] flex flex-col items-center justify-center relative overflow-hidden group h-[240px] text-center">
      <div className="absolute top-[-20%] right-[-10%] opacity-[0.03] group-hover:opacity-10 transition-opacity duration-500 rotate-12">{React.cloneElement(icon, { size: 180 })}</div>
      <div className="p-5 bg-black/40 rounded-2xl border border-white/5 group-hover:border-primary/30 transition-colors shadow-inner mb-6">{React.cloneElement(icon, { className: colors[color] })}</div>
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">{label}</p>
      <p className="text-3xl font-data-mono font-black text-white tracking-tighter">{value}</p>
      <div className="flex items-center gap-2 mt-4"><ShieldCheck size={14} className="text-success" /><p className="text-xs font-semibold text-gray-600 uppercase tracking-widest">{sub}</p></div>
    </motion.div>
  );
};

const CategoryItem = ({ title, icon, children, isOpen, onClick }) => (
  <div className="border border-white/5 rounded-2xl overflow-hidden bg-black/20 transition-all">
    <button onClick={onClick} className={`w-full p-5 flex items-center justify-between hover:bg-white/5 transition-colors ${isOpen ? 'bg-white/5' : ''}`}>
      <div className="flex items-center gap-4">
        <span className={isOpen ? 'text-primary' : 'text-gray-500'}>{icon}</span>
        <span className="text-sm font-bold uppercase tracking-widest text-white">{title}</span>
      </div>
      <ChevronDown size={18} className={`transition-transform ${isOpen ? 'rotate-180 text-primary' : 'text-gray-600'}`} />
    </button>
    <AnimatePresence>
      {isOpen && (
        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden border-t border-white/5">
          <div className="p-6 space-y-5 bg-gradient-to-b from-white/5 to-transparent">{children}</div>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);

const ConfigInput = ({ label, value, onChange, ...props }) => (
  <div className="space-y-2">
    <label className="text-xs font-semibold text-gray-400 uppercase tracking-widest ml-1">{label}</label>
    <input {...props} value={value} onChange={e => onChange(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-sm font-data-mono font-bold text-white outline-none focus:border-primary transition-all shadow-inner" />
  </div>
);

const Select = ({ label, value, options, onChange }) => (
  <div className="space-y-2">
    <label className="text-xs font-semibold text-gray-400 uppercase tracking-widest ml-1">{label}</label>
    <select value={value} onChange={e => onChange(e.target.value)} className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3.5 text-sm font-data-mono font-bold text-white outline-none focus:border-primary transition-all shadow-inner cursor-pointer">
      {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
    </select>
  </div>
);

export default App;
