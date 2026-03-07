import { useEffect, useState } from 'react'

// --- 型定義 ---
interface Photo {
  ShootingDate: string;
  displayUrl: string;
  S3Key: string;
}

function App() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);

  // 現在の表示年月を管理（初期値は現在時刻）
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() + 1 };
  });

  const API_BASE_URL = "https://yvnmn6vrel.execute-api.ap-northeast-1.amazonaws.com/photos";
  const USER_ID = "yasu";

  // 月を移動するロジック
  const changeMonth = (offset: number) => {
    setCurrentMonth(prev => {
      let m = prev.month + offset;
      let y = prev.year;
      if (m > 12) { m = 1; y++; }
      else if (m < 1) { m = 12; y--; }
      return { year: y, month: m };
    });
  };

  useEffect(() => {
    const fetchPhotos = async () => {
      setLoading(true);
      try {
        // バックエンドが期待する "YYYY-MM" 形式を作成
        const monthStr = `${currentMonth.year}-${String(currentMonth.month).padStart(2, '0')}`;
        const response = await fetch(`${API_BASE_URL}?userId=${USER_ID}&yearMonth=${monthStr}`);
        
        if (!response.ok) throw new Error("Network response was not ok");
        
        const data = await response.json();
        setPhotos(data);
      } catch (error) {
        console.error("Fetch error:", error);
        setPhotos([]); // エラー時は空にする
      } finally {
        setLoading(false);
      }
    };
    fetchPhotos();
  }, [currentMonth]); // 月が変更されるたびに実行

  return (
    <div style={containerStyle}>
      <header style={headerStyle}>
        <h1 style={{ margin: 0 }}>📸 {USER_ID}のPhotolog</h1>
        
        <div style={navStyle}>
          <button onClick={() => changeMonth(-1)} style={buttonStyle}>◀ 前月</button>
          <span style={monthDisplayStyle}>{currentMonth.year}年 {currentMonth.month}月</span>
          <button onClick={() => changeMonth(1)} style={buttonStyle}>次月 ▶</button>
        </div>
      </header>

      {loading ? (
        <div style={messageStyle}>データを読み込み中...</div>
      ) : photos.length === 0 ? (
        <div style={messageStyle}>この月の写真はありません。</div>
      ) : (
        <div style={gridStyle}>
          {photos.map((photo) => (
            <div 
              key={photo.S3Key} 
              onClick={() => setSelectedPhoto(photo)}
              style={photoCardStyle}
            >
              <img 
                src={photo.displayUrl} 
                alt="thumbnail" 
                style={imgStyle} 
                loading="lazy"
              />
              <div style={dateLabelStyle}>{photo.ShootingDate.split('T')[0]}</div>
            </div>
          ))}
        </div>
      )}

      {/* モーダル表示 */}
      {selectedPhoto && (
        <div style={modalOverlayStyle} onClick={() => setSelectedPhoto(null)}>
          <div style={modalContentStyle}>
            <img src={selectedPhoto.displayUrl} alt="full" style={modalImgStyle} />
            <p style={{ color: 'white' }}>{selectedPhoto.ShootingDate.replace('T', ' ')}</p>
          </div>
        </div>
      )}
    </div>
  );
}

// --- スタイル定義（Tailwind未導入のためJSオブジェクトで定義） ---
const containerStyle: React.CSSProperties = { padding: '20px', maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'stretch' };
const headerStyle: React.CSSProperties = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', borderBottom: '2px solid #eee', paddingBottom: '10px' };
const navStyle: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: '20px' };
const buttonStyle: React.CSSProperties = { padding: '8px 16px', cursor: 'pointer', borderRadius: '4px', border: '1px solid #ccc', background: '#999' };
const monthDisplayStyle: React.CSSProperties = { fontSize: '1.2rem', fontWeight: 'bold', minWidth: '120px', textAlign: 'center' };
const gridStyle: React.CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '15px' };
const photoCardStyle: React.CSSProperties = { border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', cursor: 'pointer', transition: 'transform 0.2s' };
const imgStyle: React.CSSProperties = { width: '100%', height: '150px', objectFit: 'cover', display: 'block' };
const dateLabelStyle: React.CSSProperties = { padding: '5px', fontSize: '10px', color: '#888', textAlign: 'right' };
const messageStyle: React.CSSProperties = { textAlign: 'center', marginTop: '100px', fontSize: '1.2rem', color: '#666' };
const modalOverlayStyle: React.CSSProperties = { position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0,0,0,0.9)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 };
const modalContentStyle: React.CSSProperties = { position: 'relative', textAlign: 'center', maxWidth: '90%' };
const modalImgStyle: React.CSSProperties = { maxWidth: '100%', maxHeight: '85vh', borderRadius: '4px' };

export default App;