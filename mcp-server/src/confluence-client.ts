import axios, { AxiosInstance } from 'axios';

interface ConfluenceConfig {
  baseUrl: string;
  email: string;
  apiToken: string;
  spaceKey: string;
}

interface SearchResult {
  id: string;
  title: string;
  content: string;
  excerpt: string;
  url: string;
  space: string;
  relevance_score?: number;
}

interface PageResult {
  id: string;
  title: string;
  content: string;
  body: string;
  url: string;
  space: string;
}

export class ConfluenceClient {
  private client: AxiosInstance;
  private config: ConfluenceConfig;

  constructor(config: ConfluenceConfig) {
    this.config = config;

    // Create authenticated Axios client
    this.client = axios.create({
      baseURL: `${config.baseUrl}/wiki/rest/api`,
      auth: {
        username: config.email,
        password: config.apiToken
      },
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      timeout: 10000
    });
  }

  /**
   * Search Confluence for content matching the query
   */
  async search(query: string, maxResults: number = 5): Promise<SearchResult[]> {
    try {
      // Build CQL (Confluence Query Language) query
      const cql = this.config.spaceKey 
        ? `text ~ "${query}" AND space = "${this.config.spaceKey}"` 
        : `text ~ "${query}"`;

      const response = await this.client.get('/content/search', {
        params: {
          cql,
          limit: maxResults,
          expand: 'body.view,space'
        }
      });

      const results: SearchResult[] = response.data.results.map((item: any, index: number) => {
        // Extract plain text from HTML content
        const content = this.extractText(item.body?.view?.value || '');
        const excerpt = this.createExcerpt(content, 300);

        return {
          id: item.id,
          title: item.title,
          content,
          excerpt,
          url: `${this.config.baseUrl}/wiki${item._links.webui}`,
          space: item.space?.name || 'Unknown',
          relevance_score: (maxResults - index) / maxResults // Simple relevance score
        };
      });

      return results;
    } catch (error: any) {
      console.error('Confluence search error:', error.message);
      
      if (error.response?.status === 401) {
        throw new Error('Confluence authentication failed. Check credentials.');
      }
      
      if (error.response?.status === 404) {
        throw new Error('Confluence API endpoint not found. Check base URL.');
      }

      throw new Error(`Confluence search failed: ${error.message}`);
    }
  }

  /**
   * Get a specific Confluence page by ID
   */
  async getPage(pageId: string): Promise<PageResult | null> {
    try {
      const response = await this.client.get(`/content/${pageId}`, {
        params: {
          expand: 'body.storage,space'
        }
      });

      const page = response.data;
      const content = this.extractText(page.body?.storage?.value || '');

      return {
        id: page.id,
        title: page.title,
        content,
        body: content,
        url: `${this.config.baseUrl}/wiki${page._links.webui}`,
        space: page.space?.name || 'Unknown'
      };
    } catch (error: any) {
      console.error('Confluence get page error:', error.message);
      
      if (error.response?.status === 404) {
        return null;
      }

      throw new Error(`Failed to get Confluence page: ${error.message}`);
    }
  }

  /**
   * Extract plain text from HTML content
   */
  private extractText(html: string): string {
    // Remove HTML tags
    let text = html.replace(/<[^>]*>/g, ' ');
    
    // Decode HTML entities
    text = text
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'");
    
    // Clean up whitespace
    text = text.replace(/\s+/g, ' ').trim();
    
    return text;
  }

  /**
   * Create an excerpt from content
   */
  private createExcerpt(content: string, maxLength: number): string {
    if (content.length <= maxLength) {
      return content;
    }
    
    const excerpt = content.substring(0, maxLength);
    const lastSpace = excerpt.lastIndexOf(' ');
    
    return lastSpace > 0 
      ? excerpt.substring(0, lastSpace) + '...' 
      : excerpt + '...';
  }
}
