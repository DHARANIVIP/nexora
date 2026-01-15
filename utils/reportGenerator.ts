/**
 * Report Generator Utility
 * Generates comprehensive HTML reports with video screenshots and forensic analysis data
 */

interface FrameData {
  timestamp: number;
  ai_probability: number;
  fft_anomaly: number;
  thumbnail?: string;
}

interface ScanReport {
  scan_id: string;
  verdict: 'DEEPFAKE' | 'REAL' | 'UNCERTAIN';
  confidence_score: number;
  total_frames_analyzed: number;
  frame_data: FrameData[];
  file_name?: string;
  created_at?: number;
  has_thumbnails?: boolean;
}

/**
 * Captures a screenshot from a video element
 */
export function captureVideoScreenshot(videoElement: HTMLVideoElement): string | null {
  try {
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.9);
  } catch (error) {
    console.error('Failed to capture video screenshot:', error);
    return null;
  }
}

/**
 * Generates a comprehensive HTML report with all forensic data and thumbnails
 */
export async function generateReportHTML(report: ScanReport, pageScreenshot?: string): Promise<string> {
  const isFake = report.verdict === 'DEEPFAKE';
  const scoreColor = isFake ? '#EF4444' : '#3B82F6';
  const timestamp = report.created_at ? new Date(report.created_at * 1000).toLocaleString() : new Date().toLocaleString();


  // Fetch and embed thumbnails (Base64)
  const thumbnailItems = await Promise.all(report.frame_data
    .filter(f => f.thumbnail)
    .map(async (frame, i) => {
      try {
        const imageUrl = `http://localhost:8000/scans/${report.scan_id}/thumbnails/${frame.thumbnail}`;
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        return new Promise<string>((resolve) => {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64data = reader.result as string;
            resolve(`
                  <div class="thumbnail-item${i === 0 ? ' featured' : ''}">
                    <img src="${base64data}" alt="Frame ${i}" />
                    <div class="thumbnail-info">
                      <span>Time: ${frame.timestamp.toFixed(2)}s</span>
                      <span>AI: ${(frame.ai_probability * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                `);
          };
          reader.readAsDataURL(blob);
        });
      } catch (e) {
        console.warn("Failed to embed thumbnail", e);
        // Fallback to URL if fetch fails
        return `
          <div class="thumbnail-item${i === 0 ? ' featured' : ''}">
             <img src="http://localhost:8000/scans/${report.scan_id}/thumbnails/${frame.thumbnail}" alt="Frame ${i}" />
             <div class="thumbnail-info">
               <span>Time: ${frame.timestamp.toFixed(2)}s</span>
               <span>AI: ${(frame.ai_probability * 100).toFixed(1)}%</span>
             </div>
           </div>
         `;
      }
    }));

  const thumbnailsHTML = thumbnailItems.join('');


  // Generate frame data table
  const frameTableHTML = report.frame_data.map((frame, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${frame.timestamp.toFixed(2)}s</td>
      <td>${(frame.ai_probability * 100).toFixed(2)}%</td>
      <td>${frame.fft_anomaly.toFixed(2)}</td>
    </tr>
  `).join('');

  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Forensic Analysis Report - ${report.scan_id}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: #FDFDFD;
      color: #1e293b;
      padding: 40px 20px;
      line-height: 1.6;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      padding: 60px;
      border-radius: 16px;
      box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .header {
      border-bottom: 3px solid #e2e8f0;
      padding-bottom: 30px;
      margin-bottom: 40px;
    }
    .logo {
      font-size: 28px;
      font-weight: 900;
      color: #3b82f6;
      margin-bottom: 10px;
    }
    h1 {
      font-size: 32px;
      font-weight: 800;
      margin-bottom: 10px;
      color: #0f172a;
    }
    .meta {
      display: flex;
      gap: 30px;
      flex-wrap: wrap;
      font-size: 14px;
      color: #64748b;
      margin-top: 15px;
    }
    .meta-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .meta-label {
      font-weight: 600;
      color: #475569;
    }
    .video-preview {
      margin: 30px 0;
      border-radius: 12px;
      overflow: hidden;
      border: 2px solid #e2e8f0;
      background: #000;
    }
    .video-preview img {
      width: 100%;
      height: auto;
      display: block;
    }
    .video-caption {
      background: #f8fafc;
      padding: 12px 20px;
      font-size: 13px;
      color: #64748b;
      font-weight: 600;
      text-align: center;
      border-top: 1px solid #e2e8f0;
    }
    .verdict-section {
      background: linear-gradient(135deg, ${isFake ? '#fee2e2' : '#dbeafe'} 0%, white 100%);
      border: 2px solid ${isFake ? '#fecaca' : '#bfdbfe'};
      border-radius: 12px;
      padding: 40px;
      margin: 40px 0;
      text-align: center;
    }
    .verdict-badge {
      display: inline-block;
      padding: 12px 24px;
      border-radius: 8px;
      font-weight: 800;
      font-size: 18px;
      text-transform: uppercase;
      letter-spacing: 1px;
      background: ${scoreColor};
      color: white;
      margin-bottom: 20px;
    }
    .confidence-score {
      font-size: 72px;
      font-weight: 900;
      color: ${scoreColor};
      margin: 20px 0;
    }
    .confidence-label {
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 2px;
      color: #64748b;
      font-weight: 700;
    }
    .section {
      margin: 50px 0;
    }
    .section-title {
      font-size: 20px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid #e2e8f0;
    }
    .thumbnails-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 20px;
      margin-top: 20px;
    }
    .thumbnail-item {
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      overflow: hidden;
      background: white;
    }
    .thumbnail-item.featured {
      grid-column: 1 / -1;
      max-width: 800px;
      margin: 0 auto 30px;
    }
    .thumbnail-item.featured img {
      width: 100%;
      height: 400px;
      object-fit: contain;
      background: #000;
    }
    .thumbnail-item img {
      width: 100%;
      height: 150px;
      object-fit: cover;
      display: block;
    }
    .thumbnail-info {
      padding: 10px;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      background: #f8fafc;
      color: #64748b;
      font-weight: 600;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 20px;
      font-size: 14px;
    }
    th {
      background: #f1f5f9;
      padding: 12px;
      text-align: left;
      font-weight: 700;
      color: #475569;
      border-bottom: 2px solid #cbd5e1;
    }
    td {
      padding: 12px;
      border-bottom: 1px solid #e2e8f0;
    }
    tr:hover {
      background: #f8fafc;
    }
    .footer {
      margin-top: 60px;
      padding-top: 30px;
      border-top: 2px solid #e2e8f0;
      text-align: center;
      color: #94a3b8;
      font-size: 13px;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 20px;
      margin: 30px 0;
    }
    .stat-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
    }
    .stat-value {
      font-size: 32px;
      font-weight: 800;
      color: #0f172a;
      margin-bottom: 5px;
    }
    .stat-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #64748b;
      font-weight: 600;
    }
    @media print {
      body { padding: 0; }
      .container { box-shadow: none; padding: 40px; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">🔍 DETECTIVE AI</div>
      <h1>Deepfake Forensic Analysis Report</h1>
      <div class="meta">
        <div class="meta-item">
          <span class="meta-label">Case ID:</span>
          <span>${report.scan_id}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">File:</span>
          <span>${report.file_name || 'Unknown'}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Generated:</span>
          <span>${timestamp}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Frames Analyzed:</span>
          <span>${report.total_frames_analyzed}</span>
        </div>
      </div>
    </div>

    ${pageScreenshot ? `
    <div class="section">
      <h2 class="section-title">📊 Forensic Scan Page View</h2>
      <div class="video-preview">
        <img src="${pageScreenshot}" alt="Forensic Scan Page" />
        <div class="video-caption">Complete Analysis Interface Screenshot</div>
      </div>
    </div>
    ` : ''}

    <div class="verdict-section">
      <div class="verdict-badge">${report.verdict}</div>
      <div class="confidence-score">${Math.round(report.confidence_score)}%</div>
      <div class="confidence-label">Detection Confidence</div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">${report.total_frames_analyzed}</div>
        <div class="stat-label">Frames Analyzed</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${(report.frame_data.filter(f => f.ai_probability > 0.5).length / report.frame_data.length * 100).toFixed(0)}%</div>
        <div class="stat-label">Anomaly Rate</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${(report.frame_data.reduce((sum, f) => sum + f.ai_probability, 0) / report.frame_data.length * 100).toFixed(1)}%</div>
        <div class="stat-label">Avg AI Score</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">${(report.frame_data.reduce((sum, f) => sum + f.fft_anomaly, 0) / report.frame_data.length).toFixed(1)}</div>
        <div class="stat-label">Avg FFT Score</div>
      </div>
    </div>

    ${thumbnailsHTML ? `
    <div class="section">
      <h2 class="section-title">📸 Analyzed Frame Samples</h2>
      <div class="thumbnails-grid">
        ${thumbnailsHTML}
      </div>
    </div>
    ` : ''}

    <div class="section">
      <h2 class="section-title">📊 Detailed Frame Analysis</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Timestamp</th>
            <th>AI Probability</th>
            <th>FFT Anomaly</th>
          </tr>
        </thead>
        <tbody>
          ${frameTableHTML}
        </tbody>
      </table>
    </div>

    <div class="footer">
      <p><strong>DETECTIVE AI Forensic Analysis System</strong></p>
      <p>This report was generated using advanced AI and mathematical analysis techniques.</p>
      <p>Report ID: ${report.scan_id} | Generated: ${timestamp}</p>
    </div>
  </div>
</body>
</html>
  `.trim();
}

/**
 * Downloads the generated report as an HTML file
 */
export function downloadReport(html: string, filename: string): void {
  const blob = new Blob([html], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}


