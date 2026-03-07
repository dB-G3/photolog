import { useEffect, useState } from 'react'

interface Photo {
  ShootingDate: string;
  displayUrl: string;
  S3Key: string;
}

function App() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);

  const API_BASE_URL = "https://yvnmn6vrel.execute-api.ap-northeast-1.amazonaws.com/photos";
  const USER_ID = "yasu";

  // 画像拡大表示状態管理用
  const [selectedPhoto, setSelectedPhoto] = useState<Photo | null>(null);

  useEffect(() => {
    const fetchPhotos = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}?userId=${USER_ID}`);
        const data = await response.json();
        setPhotos(data);
      } catch (error) {
        console.error("Fetch error:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchPhotos();
  }, []);

  if (loading) return <div style={{ padding: '20px' }}>読み込み中...</div>;

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>📸 Photolog</h1>
      
      {/* ギャラリー部分 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '15px'
      }}>
        {photos.map((photo) => (
          <div 
            key={photo.S3Key} 
            onClick={() => setSelectedPhoto(photo)} // クリックで選択
            style={{ border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden', cursor: 'pointer' }}
          >
            <img 
              src={photo.displayUrl} 
              alt="photo" 
              style={{ width: '100%', height: 'auto', display: 'block' }} 
            />
          </div>
        ))}
      </div>

      {/* --- ここからモーダル部分 --- */}
      {selectedPhoto && (
        <div 
          onClick={() => setSelectedPhoto(null)} // 背景クリックで閉じる
          style={{
            position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
            backgroundColor: 'rgba(0,0,0,0.85)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000, cursor: 'zoom-out'
          }}
        >
          <div style={{ position: 'relative', maxWidth: '90%', maxHeight: '90%' }}>
            <img 
              src={selectedPhoto.displayUrl} 
              alt="original"
              style={{ maxWidth: '100%', maxHeight: '90vh', boxShadow: '0 0 20px rgba(0,0,0,0.5)' }}
            />
            <div style={{ color: 'white', marginTop: '10px', textAlign: 'center' }}>
              {selectedPhoto.ShootingDate.split('T')[0]}
            </div>
            <button 
              onClick={() => setSelectedPhoto(null)}
              style={{
                position: 'absolute', top: '-40px', right: '0',
                background: 'none', border: 'none', color: 'white', fontSize: '30px', cursor: 'pointer'
              }}
            >
              ×
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App