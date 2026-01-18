import express, { Request, Response } from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { ConfluenceClient } from './confluence-client';

dotenv.config();

const app = express();
const port = process.env.PORT || 3001;

// Initialize Confluence client
const confluenceClient = new ConfluenceClient({
  baseUrl: process.env.CONFLUENCE_BASE_URL || '',
  email: process.env.CONFLUENCE_EMAIL || '',
  apiToken: process.env.CONFLUENCE_API_TOKEN || '',
  spaceKey: process.env.CONFLUENCE_SPACE_KEY || ''
});

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({ 
    status: 'ok', 
    service: 'Confluence MCP Server',
    timestamp: new Date().toISOString()
  });
});

// Search endpoint
app.post('/search', async (req: Request, res: Response) => {
  try {
    const { query, max_results = 5 } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Query parameter is required' });
    }

    console.log(`[MCP Server] Searching Confluence for: "${query}" (max_results: ${max_results})`);

    const results = await confluenceClient.search(query, max_results);

    console.log(`[MCP Server] Found ${results.length} results`);

    res.json({
      query,
      count: results.length,
      results
    });
  } catch (error: any) {
    console.error('[MCP Server] Search error:', error.message);
    res.status(500).json({ 
      error: 'Search failed', 
      message: error.message 
    });
  }
});

// Get page by ID endpoint
app.get('/page/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;

    if (!id) {
      return res.status(400).json({ error: 'Page ID is required' });
    }

    console.log(`[MCP Server] Fetching page: ${id}`);

    const page = await confluenceClient.getPage(id);

    if (!page) {
      return res.status(404).json({ error: 'Page not found' });
    }

    console.log(`[MCP Server] Retrieved page: ${page.title}`);

    res.json(page);
  } catch (error: any) {
    console.error('[MCP Server] Get page error:', error.message);
    
    if (error.response?.status === 404) {
      return res.status(404).json({ error: 'Page not found' });
    }

    res.status(500).json({ 
      error: 'Failed to retrieve page', 
      message: error.message 
    });
  }
});

// Start server
app.listen(port, () => {
  console.log(`
╔═══════════════════════════════════════════════════════════╗
║         Confluence MCP Server Running                     ║
╚═══════════════════════════════════════════════════════════╝

📡 Server URL: http://localhost:${port}
🏥 Health Check: http://localhost:${port}/health
🔍 Search Endpoint: POST http://localhost:${port}/search
📄 Page Endpoint: GET http://localhost:${port}/page/:id

🔧 Configuration:
   - Confluence URL: ${process.env.CONFLUENCE_BASE_URL || 'NOT SET'}
   - Space Key: ${process.env.CONFLUENCE_SPACE_KEY || 'NOT SET'}
   - Email: ${process.env.CONFLUENCE_EMAIL || 'NOT SET'}

${!process.env.CONFLUENCE_BASE_URL || !process.env.CONFLUENCE_API_TOKEN 
  ? '⚠️  WARNING: Confluence credentials not configured!\n   Please create .env file from .env.example\n' 
  : '✅ Confluence credentials configured'}
`);
});
