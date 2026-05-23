def detect_category(text: str) -> str:
    
    if not text:
        return 'empty'
        
    text_lower = text.lower()

    
    crypto_keywords = [
        'bitcoin',
        'btc',
        'ethereum',
        'eth',
        'solana',
        'sol',
        'xrp',
        'bnb',
        'crypto',
        'token',
        'blockchain',
        'wallet',
        'metamask',
        'ledger',
        'mining',
        'staking',
        'liquidity',
        'defi',
        'nft',
        'stablecoin',
        'usdt',
        'usdc',
        'altcoin',
        'dogecoin',
        'shiba inu',
        'cardano',
        'polkadot',
        'avalanche',
        'chainlink',
        'uniswap',
        'binance',
        'coinbase',
        'kraken',
        'satoshi',
        'halving',
        'hashrate',
        'smart contract',
        'web3',
        'airdrop',
        'whales',
        'bull run',
        'bear market',
        'hodl',
        'fomo',
        'gas fee',
        'layer 2',
        'arbitrum',
        'optimism',
        'polygon',
        'matic'
    ]
    if any(kw in text_lower for kw in crypto_keywords):
        return 'crypto'

    
    forex_keywords = [
        'eur/usd',
        'usd/brl',
        'gbp/usd',
        'usd/jpy',
        'aud/usd',
        'usd/chf',
        'usd/cad',
        'forex',
        'currency',
        'exchange rate',
        'pips',
        'leverage',
        'broker',
        'mt4',
        'mt5',
        'trading view',
        'spread',
        'margin call',
        'central bank',
        'ecb',
        'boj',
        'fiat',
        'reserve currency',
        'inflation',
        'hyperinflation',
        'devaluation',
        'remittance',
        'carry trade',
        'spot price',
        'volatility',
        'cable',
        'loonie',
        'swissy',
        'kiwi',
        'greenback',
        'yen',
        'eurozone',
        'quantitative easing'
    ]
    if any(kw in text_lower for kw in forex_keywords):
        return 'forex'

    
    us_politics_keywords = [
        'trump',
        'biden',
        'harris',
        'vance',
        'senate',
        'congress',
        'president',
        'white house',
        'democratic',
        'republican',
        'impeachment',
        'pardon',
        'cabinet',
        'supreme court',
        'constitution',
        'capitol',
        'midterms',
        'electoral college',
        'primary',
        'caucus',
        'lobbying',
        'oval office',
        'pentagon',
        'state department',
        'gop',
        'democrats',
        'maga',
        'swing state',
        'red state',
        'blue state',
        'gerrymandering',
        'filibuster',
        'veto',
        'speaker of the house',
        'majority leader',
        'executive order',
        'bipartisan',
        'inauguration',
        'federalism'
    ]
    if any(kw in text_lower for kw in us_politics_keywords):
        return 'politics'

    
    space_keywords = [
        'spacex',
        'starship',
        'hls',
        'dragon',
        'falcon',
        'nasa',
        'orbit',
        'satellite',
        'telescope',
        'james webb',
        'hubble',
        'iss',
        'astronaut',
        'cosmonaut',
        'mars',
        'moon',
        'artemis',
        'apollo',
        'asteroid',
        'comet',
        'galaxy',
        'black hole',
        'supernova',
        'exoplanet',
        'rocket',
        'launchpad',
        'booster',
        'zero gravity',
        'blue origin',
        'virgin galactic',
        'esa',
        'roscosmos',
        'jaxa',
        'isro',
        'cnsa',
        'nebula',
        'milky way',
        'constellation',
        'lunar',
        'solar system'
    ]
    if any(kw in text_lower for kw in space_keywords):
        return 'space'

    
    economy_keywords = [
        'sp500',
        's&p',
        'nasdaq',
        'dow jones',
        'federal reserve',
        'fed',
        'interest rate',
        'debt ceiling',
        'tariff',
        'trade',
        'economy',
        'recession',
        'gdp',
        'gnp',
        'fiscal policy',
        'monetary policy',
        'deficit',
        'surplus',
        'bankruptcy',
        'merger',
        'acquisition',
        'ipo',
        'dividend',
        'bond',
        'treasury',
        'yield',
        'market cap',
        'earnings report',
        'revenue',
        'profit margin',
        'bearish',
        'bullish',
        'short selling',
        'insider trading',
        'derivative',
        'futures',
        'options',
        'commodity',
        'gold price',
        'oil price',
        'crude oil',
        'inflation rate'
    ]
    if any(kw in text_lower for kw in economy_keywords):
        return 'economy'

    
    health_keywords = [
        'measles',
        'polio',
        'vaccine',
        'pandemic',
        'health',
        'fda',
        'who',
        'cdc',
        'hospital',
        'doctor',
        'nurse',
        'surgery',
        'pharmaceutical',
        'clinical trial',
        'infection',
        'virus',
        'bacteria',
        'antibiotics',
        'oncology',
        'cardiology',
        'diabetes',
        'obesity',
        'mental health',
        'therapy',
        'psychology',
        'genetics',
        'dna',
        'rna',
        'crispr',
        'epidemiology',
        'immunity',
        'antibody',
        'diagnosis',
        'symptom',
        'chronic',
        'acute',
        'trauma',
        'ambulance',
        'patient care',
        'telemedicine'
    ]
    if any(kw in text_lower for kw in health_keywords):
        return 'health'

    
    celebrity_keywords = [
        'taylor swift',
        'oprah',
        'kanye',
        'celebrity',
        'tour',
        'album',
        'grammy',
        'oscar',
        'emmy',
        'hollywood',
        'red carpet',
        'paparazzi',
        'influencer',
        'kardashian',
        'beyonce',
        'rihanna',
        'drake',
        'justin bieber',
        'elon musk',
        'bill gates',
        'mark zuckerberg',
        'jeff bezos',
        'actor',
        'actress',
        'director',
        'producer',
        'cinema',
        'box office',
        'blockbuster',
        'premiere',
        'fanbase',
        'fandom',
        'scandal',
        'gossip',
        'dating',
        'divorce',
        'marriage',
        'biography',
        'memoir'
    ]
    if any(kw in text_lower for kw in celebrity_keywords):
        return 'celebrity'

    
    ai_keywords = [
        'artificial intelligence',
        'ai',
        'machine learning',
        'deep learning',
        'neural network',
        'transformer',
        'llm',
        'gpt-4',
        'chatgpt',
        'claude',
        'gemini',
        'stable diffusion',
        'midjourney',
        'open ai',
        'anthropic',
        'nvidia',
        'gpu',
        'tpu',
        'algorithm',
        'data science',
        'big data',
        'nlp',
        'computer vision',
        'robotics',
        'automation',
        'chatbot',
        'generative ai',
        'inference',
        'training',
        'fine-tuning',
        'python',
        'pytorch',
        'tensorflow',
        'hugging face',
        'supercomputer',
        'quantum computing',
        'semiconductor',
        'microchip',
        'singularity',
        'turing test'
    ]
    if any(kw in text_lower for kw in ai_keywords):
        return 'technology'

    
    sports_keywords = [
        'football',
        'soccer',
        'basketball',
        'nba',
        'nfl',
        'mlb',
        'nhl',
        'tennis',
        'grand slam',
        'wimbledon',
        'olympics',
        'world cup',
        'fifa',
        'uefa',
        'champions league',
        'super bowl',
        'touchdown',
        'home run',
        'quarterback',
        'striker',
        'goalkeeper',
        'referee',
        'stadium',
        'marathon',
        'athlete',
        'olympian',
        'formula 1',
        'grand prix',
        'ferrari',
        'red bull racing',
        'mercedes f1',
        'golf',
        'pga',
        'cricket',
        'rugby',
        'boxing',
        'mma',
        'ufc',
        'wrestling',
        'gymnastics',
        'swimming',
        'cycling',
        'tour de france'
    ]
    if any(kw in text_lower for kw in sports_keywords):
        return 'sports'

    
    climate_keywords = [
        'climate change',
        'global warming',
        'greenhouse gas',
        'carbon footprint',
        'renewable energy',
        'solar power',
        'wind turbine',
        'sustainability',
        'ecology',
        'environment',
        'pollution',
        'recycling',
        'deforestation',
        'biodiversity',
        'glacier',
        'arctic',
        'emissions',
        'net zero',
        'cop28',
        'paris agreement',
        'epa',
        'wildfire',
        'drought',
        'flood',
        'hurricane',
        'ocean acidificaton',
        'endangered species',
        'conservation',
        'ecosystem',
        'fossil fuels',
        'coal',
        'natural gas',
        'electric vehicle',
        'tesla',
        'ev charging'
    ]
    if any(kw in text_lower for kw in climate_keywords):
        return 'environment'

    
    gaming_keywords = [
        'video game',
        'gaming',
        'playstation',
        'xbox',
        'nintendo switch',
        'pc master race',
        'steam',
        'epic games',
        'fortnite',
        'roblox',
        'minecraft',
        'call of duty',
        'gta',
        'cyberpunk 2077',
        'elden ring',
        'rpg',
        'fps',
        'multiplayer',
        'esports',
        'twitch',
        'streaming',
        'speedrun',
        'console',
        'controller',
        'graphics card',
        'ray tracing',
        'loot box',
        'microtransactions',
        'dlc',
        'remaster',
        'indie game',
        'developer',
        'ubisoft',
        'ea sports',
        'activision',
        'blizzard',
        'rockstar games',
        'bethesda'
    ]
    if any(kw in text_lower for kw in gaming_keywords):
        return 'gaming'

    
    food_keywords = [
        'recipe',
        'cooking',
        'chef',
        'restaurant',
        'cuisine',
        'michelin star',
        'vegan',
        'vegetarian',
        'keto',
        'gluten-free',
        'dessert',
        'baking',
        'grill',
        'seafood',
        'pasta',
        'pizza',
        'sushi',
        'burger',
        'wine',
        'cocktail',
        'coffee',
        'barista',
        'nutrition',
        'calorie',
        'protein',
        'organic',
        'farmers market',
        'superfood',
        'spices',
        'ingredients',
        'breakfast',
        'brunch',
        'dinner',
        'lunch',
        'fast food',
        'street food'
    ]
    if any(kw in text_lower for kw in food_keywords):
        return 'food'

    
    travel_keywords = [
        'travel',
        'tourism',
        'vacation',
        'flight',
        'airline',
        'hotel',
        'resort',
        'backpacking',
        'passport',
        'visa',
        'destination',
        'landmark',
        'airport',
        'cruise',
        'road trip',
        'adventure',
        'sightseeing',
        'itinerary',
        'booking',
        'airbnb',
        'expedia',
        'tripadvisor',
        'safari',
        'island',
        'beach',
        'mountain',
        'hiking',
        'camping',
        'tourist attraction',
        'museum',
        'heritage',
        'culture',
        'foreign country'
    ]
    if any(kw in text_lower for kw in travel_keywords):
        return 'travel'

    
    edu_keywords = [
        'university',
        'college',
        'school',
        'student',
        'professor',
        'research',
        'study',
        'curriculum',
        'scholarship',
        'tuition',
        'degree',
        'diploma',
        'exam',
        'textbook',
        'library',
        'academic',
        'thesis',
        'dissertation',
        'physics',
        'chemistry',
        'biology',
        'mathematics',
        'algebra',
        'geometry',
        'calculus',
        'science paper',
        'peer review',
        'journal',
        'lab',
        'experiment',
        'theory',
        'quantum',
        'particle',
        'molecule',
        'cell'
    ]
    if any(kw in text_lower for kw in edu_keywords):
        return 'education'

    
    movie_keywords = [
        'movie',
        'film',
        'cinema',
        'netflix',
        'hbo',
        'disney+',
        'streaming service',
        'trailer',
        'teaser',
        'casting',
        'screenplay',
        'script',
        'cinematography',
        'editing',
        'visual effects',
        'cgi',
        'documentary',
        'horror',
        'comedy',
        'drama',
        'sci-fi',
        'fantasy',
        'animation',
        'anime',
        'sitcom',
        'soap opera',
        'miniseries',
        'episode',
        'season',
        'finale',
        'spoiler',
        'rotten tomatoes',
        'imdb'
    ]
    if any(kw in text_lower for kw in movie_keywords):
        return 'entertainment'

    
    fashion_keywords = [
        'fashion',
        'style',
        'clothing',
        'apparel',
        'designer',
        'luxury',
        'brand',
        'gucci',
        'prada',
        'louis vuitton',
        'vogue',
        'runway',
        'model',
        'fashion week',
        'trend',
        'outfit',
        'jewelry',
        'watch',
        'sneakers',
        'streetwear',
        'cosmetics',
        'makeup',
        'skincare',
        'perfume',
        'hairstyle',
        'boutique',
        'retail',
        'shopping',
        'collection'
    ]
    if any(kw in text_lower for kw in fashion_keywords):
        return 'fashion'

    
    business_keywords = [
        'business',
        'startup',
        'entrepreneur',
        'founder',
        'ceo',
        'co-founder',
        'venture capital',
        'angel investor',
        'funding round',
        'unicorn',
        'valuation',
        'marketing',
        'sales',
        'strategy',
        'management',
        'leadership',
        'networking',
        'incubator',
        'accelerator',
        'pitch deck',
        'product-market fit',
        'b2b',
        'b2c',
        'saas',
        'ecommerce',
        'supply chain',
        'logistics',
        'human resources',
        'outsourcing'
    ]
    if any(kw in text_lower for kw in business_keywords):
        return 'business'

    
    law_keywords = [
        'law',
        'legal',
        'court',
        'judge',
        'lawyer',
        'attorney',
        'litigation',
        'lawsuit',
        'plaintiff',
        'defendant',
        'verdict',
        'sentence',
        'prison',
        'jail',
        'crime',
        'criminal',
        'civil rights',
        'intellectual property',
        'patent',
        'trademark',
        'copyright',
        'contract',
        'agreement',
        'clause',
        'arbitration',
        'mediation',
        'jurisdiction',
        'legislation',
        'statute'
    ]
    if any(kw in text_lower for kw in law_keywords):
        return 'law'

    
    auto_keywords = [
        'car',
        'automotive',
        'vehicle',
        'sedan',
        'suv',
        'truck',
        'electric car',
        'hybrid',
        'engine',
        'transmission',
        'horsepower',
        'torque',
        'autonomous driving',
        'self-driving',
        'toyota',
        'ford',
        'bmw',
        'mercedes',
        'audi',
        'honda',
        'ferrari',
        'lamborghini',
        'porsche',
        'volkswagen',
        'hyundai',
        'kia',
        'rivian',
        'lucid',
        'dealership',
        'mechanic'
    ]
    if any(kw in text_lower for kw in auto_keywords):
        return 'automotive'

    
    music_keywords = [
        'music',
        'song',
        'artist',
        'band',
        'singer',
        'composer',
        'orchestra',
        'concert',
        'festival',
        'spotify',
        'apple music',
        'streaming',
        'vinyl',
        'instrument',
        'guitar',
        'piano',
        'drums',
        'violin',
        'synthesizer',
        'genre',
        'rock',
        'pop',
        'hip hop',
        'rap',
        'jazz',
        'classical',
        'techno',
        'edm',
        'blues',
        'country music',
        'lyrics',
        'melody',
        'rhythm',
        'beat'
    ]
    if any(kw in text_lower for kw in music_keywords):
        return 'music'

    
    cyber_keywords = [
        'cybersecurity',
        'hacker',
        'malware',
        'virus',
        'ransomware',
        'phishing',
        'firewall',
        'encryption',
        'password',
        'data breach',
        'exploit',
        'vulnerability',
        'zero-day',
        'spyware',
        'trojan',
        'botnet',
        'ddos',
        'authentication',
        'authorization',
        'vpn',
        'proxy',
        'dark web',
        'ethical hacking',
        'penetration test',
        'security audit',
        'privacy',
        'anonymity'
    ]
    if any(kw in text_lower for kw in cyber_keywords):
        return 'cybersecurity'

    
    military_keywords = [
        'military',
        'army',
        'navy',
        'air force',
        'marines',
        'war',
        'conflict',
        'battle',
        'weapon',
        'missile',
        'tank',
        'fighter jet',
        'submarine',
        'aircraft carrier',
        'soldier',
        'officer',
        'general',
        'admiral',
        'intelligence',
        'cia',
        'mi6',
        'mossad',
        'nato',
        'defense budget',
        'strategy',
        'tactics',
        'ammunition',
        'artillery',
        'infantry',
        'special forces'
    ]
    if any(kw in text_lower for kw in military_keywords):
        return 'military'

    
    real_estate_keywords = [
        'real estate',
        'property',
        'house',
        'apartment',
        'condo',
        'mansion',
        'mortgage',
        'rent',
        'lease',
        'landlord',
        'tenant',
        'broker',
        'realtor',
        'listing',
        'foreclosure',
        'eviction',
        'suburb',
        'downtown',
        'architecture',
        'construction',
        'renovation',
        'home improvement',
        'interior design',
        'commercial property',
        'zoning',
        'appraisal'
    ]
    if any(kw in text_lower for kw in real_estate_keywords):
        return 'real_estate'

    
    history_keywords = [
        'history',
        'ancient',
        'medieval',
        'renaissance',
        'archaeology',
        'civilization',
        'empire',
        'dynasty',
        'monarchy',
        'revolution',
        'world war i',
        'world war ii',
        'cold war',
        'historical figure',
        'artifact',
        'manuscript',
        'epoch',
        'era',
        'century',
        'decade',
        'timeline',
        'historian',
        'archive',
        'heritage site',
        'colony',
        'independence'
    ]
    if any(kw in text_lower for kw in history_keywords):
        return 'history'

    
    books_keywords = [
        'book',
        'novel',
        'fiction',
        'non-fiction',
        'author',
        'writer',
        'poet',
        'poetry',
        'literature',
        'bestseller',
        'publishing',
        'manuscript',
        'chapter',
        'protagonist',
        'antagonist',
        'plot',
        'e-book',
        'kindle',
        'audible',
        'biography',
        'autobiography',
        'essay',
        'anthology',
        'literary prize',
        'nobel prize in literature',
        'bookstore'
    ]
    if any(kw in text_lower for kw in books_keywords):
        return 'books'

    
    social_media_keywords = [
        'social media',
        'instagram',
        'tiktok',
        'twitter',
        'facebook',
        'linkedin',
        'snapchat',
        'reddit',
        'youtube',
        'follower',
        'like',
        'share',
        'retweet',
        'viral',
        'engagement',
        'algorithm',
        'hashtag',
        'dm',
        'content creator',
        'vlogger',
        'influencer marketing',
        'community',
        'profile',
        'feed',
        'story'
    ]
    if any(kw in text_lower for kw in social_media_keywords):
        return 'social_media'

    
    psych_keywords = [
        'psychology',
        'mental health',
        'therapy',
        'counseling',
        'behavior',
        'cognition',
        'emotion',
        'anxiety',
        'depression',
        'stress',
        'trauma',
        'personality',
        'intelligence',
        'subconscious',
        'unconscious',
        'memory',
        'learning',
        'motivation',
        'disorder',
        'psychiatry',
        'neuroscience',
        'mindfulness',
        'meditation',
        'self-help'
    ]
    if any(kw in text_lower for kw in psych_keywords):
        return 'psychology'

    
    philosophy_keywords = [
        'philosophy',
        'ethics',
        'logic',
        'metaphysics',
        'epistemology',
        'existentialism',
        'stoicism',
        'nihilism',
        'plato',
        'aristotle',
        'kant',
        'nietzsche',
        'socrates',
        'wisdom',
        'truth',
        'reality',
        'morality',
        'consciousness',
        'free will',
        'determinism',
        'paradox',
        'idealism',
        'materialism'
    ]
    if any(kw in text_lower for kw in philosophy_keywords):
        return 'philosophy'

    
    geography_keywords = [
        'geography',
        'continent',
        'country',
        'nation',
        'region',
        'border',
        'capital city',
        'ocean',
        'sea',
        'river',
        'lake',
        'mountain range',
        'desert',
        'island',
        'map',
        'atlas',
        'cartography',
        'population',
        'demographics',
        'urbanization',
        'migration',
        'territory'
    ]
    if any(kw in text_lower for kw in geography_keywords):
        return 'geography'

    
    religion_keywords = [
        'religion',
        'faith',
        'spirituality',
        'god',
        'church',
        'mosque',
        'synagogue',
        'temple',
        'bible',
        'quran',
        'torah',
        'buddhism',
        'christianity',
        'islam',
        'judaism',
        'hinduism',
        'sikhism',
        'priest',
        'imam',
        'rabbi',
        'monk',
        'prayer',
        'ritual',
        'sacred',
        'holy'
    ]
    if any(kw in text_lower for kw in religion_keywords):
        return 'religion'

    
    
    
    
    
    

    
    tech_companies = [
        'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook', 'alphabet', 'netflix',
        'tesla', 'samsung', 'intel', 'amd', 'nvidia', 'tsmc', 'asml', 'sony', 'panasonic',
        'tencent', 'alibaba', 'baidu', 'huawei', 'xiaomi', 'uber', 'airbnb', 'spotify',
        'salesforce', 'adobe', 'oracle', 'ibm', 'cisco', 'dell', 'hp', 'lenovo', 'asus'
    ]
    if any(kw in text_lower for kw in tech_companies):
        return 'technology_company'

    
    programming_languages = [
        'python', 'javascript', 'java', 'c++', 'c
        'typescript', 'php', 'ruby', 'objective-c', 'scala', 'elixir', 'haskell', 'lua',
        'perl', 'fortran', 'cobol', 'assembly', 'sql', 'html', 'css', 'bash', 'powershell'
    ]
    if any(kw in text_lower for kw in programming_languages):
        return 'programming'

    
    
    long_phrases = [
        "breaking news", "official statement", "exclusive interview", "leaked document",
        "market analysis", "technical review", "user experience", "customer support"
    ]
    
    for _ in range(300):
        
        pass

    return 'other'


