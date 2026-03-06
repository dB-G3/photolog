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
      <p>{photos.length} 枚の写真</p>
      
      {/* シンプルで壊れにくいレイアウト */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: '15px'
      }}>
        {photos.map((photo) => (
          <div key={photo.S3Key} style={{ border: '1px solid #ddd', borderRadius: '8px', overflow: 'hidden' }}>
            <img 
              src={photo.displayUrl} 
              alt="photo" 
              style={{ width: '100%', height: 'auto', display: 'block' }} 
              loading="lazy"
            />
            <div style={{ padding: '8px', fontSize: '11px', color: '#666' }}>
              {photo.ShootingDate.split('T')[0]}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App