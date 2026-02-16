import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { CookieService } from 'ngx-cookie-service';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from 'src/environments/django';
import {
  Block,
  Document,
  DocumentBlock,
  DocumentCategory,
  DocumentStatus,
  DocumentTemplate,
  DocumentTemplateBlock,
  DocumentType
} from 'src/app/models/document';

@Injectable({
  providedIn: 'root'
})
export class DocumentsApiService {
  private baseUrl = environment.production ? environment.djangoBaseUrl : environment.localhostDjango;
  private headers: HttpHeaders;

  constructor(
    private http: HttpClient,
    private cookieService: CookieService,
  ) {
    const csrf = this.cookieService.get('csrftoken') || '';
    this.headers = new HttpHeaders()
      .set('content-type', 'application/json')
      .set('X-CSRFToken', csrf);
  }

  private unwrapList<T>(response: any): T[] {
    if (Array.isArray(response)) {
      return response as T[];
    }
    if (Array.isArray(response?.results)) {
      return response.results as T[];
    }
    return [] as T[];
  }

  listTypes(): Observable<DocumentType[]> {
    return this.http.get<DocumentType[]>(`${this.baseUrl}/api/documents/types/`, { headers: this.headers })
      .pipe(map((res: any) => this.unwrapList<DocumentType>(res)));
  }

  listStatuses(): Observable<DocumentStatus[]> {
    return this.http.get<DocumentStatus[]>(`${this.baseUrl}/api/documents/statuses/`, { headers: this.headers })
      .pipe(map((res: any) => this.unwrapList<DocumentStatus>(res)));
  }

  listCategories(): Observable<DocumentCategory[]> {
    return this.http.get<DocumentCategory[]>(`${this.baseUrl}/api/documents/categories/`, { headers: this.headers })
      .pipe(map((res: any) => this.unwrapList<DocumentCategory>(res)));
  }

  listBlocks(): Observable<Block[]> {
    return this.http.get<Block[]>(`${this.baseUrl}/api/documents/blocks/`, { headers: this.headers })
      .pipe(map((res: any) => this.unwrapList<Block>(res)));
  }

  createBlock(data: Partial<Block>): Observable<Block> {
    return this.http.post<Block>(`${this.baseUrl}/api/documents/blocks/`, data, { headers: this.headers });
  }

  updateBlock(id: number, data: Partial<Block>): Observable<Block> {
    return this.http.patch<Block>(`${this.baseUrl}/api/documents/blocks/${id}/`, data, { headers: this.headers });
  }

  deleteBlock(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/api/documents/blocks/${id}/`, { headers: this.headers });
  }

  listTemplates(): Observable<DocumentTemplate[]> {
    return this.http.get<DocumentTemplate[]>(`${this.baseUrl}/api/documents/templates/`, { headers: this.headers })
      .pipe(map((res: any) => this.unwrapList<DocumentTemplate>(res)));
  }

  getTemplate(id: number): Observable<DocumentTemplate> {
    return this.http.get<DocumentTemplate>(`${this.baseUrl}/api/documents/templates/${id}/`, { headers: this.headers });
  }

  createTemplate(data: Partial<DocumentTemplate>): Observable<DocumentTemplate> {
    return this.http.post<DocumentTemplate>(`${this.baseUrl}/api/documents/templates/`, data, { headers: this.headers });
  }

  updateTemplate(id: number, data: Partial<DocumentTemplate>): Observable<DocumentTemplate> {
    return this.http.patch<DocumentTemplate>(`${this.baseUrl}/api/documents/templates/${id}/`, data, { headers: this.headers });
  }

  deleteTemplate(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/api/documents/templates/${id}/`, { headers: this.headers });
  }

  addTemplateBlock(templateId: number, data: Partial<DocumentTemplateBlock>): Observable<DocumentTemplateBlock> {
    return this.http.post<DocumentTemplateBlock>(
      `${this.baseUrl}/api/documents/templates/${templateId}/blocks/`,
      data,
      { headers: this.headers }
    );
  }

  updateTemplateBlock(id: number, data: Partial<DocumentTemplateBlock>): Observable<DocumentTemplateBlock> {
    return this.http.patch<DocumentTemplateBlock>(
      `${this.baseUrl}/api/documents/template-blocks/${id}/`,
      data,
      { headers: this.headers }
    );
  }

  deleteTemplateBlock(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/api/documents/template-blocks/${id}/`, { headers: this.headers });
  }

  reorderTemplateBlocks(templateId: number, order: Array<{ id: number; position: number }>): Observable<any> {
    return this.http.patch(
      `${this.baseUrl}/api/documents/templates/${templateId}/reorder/`,
      { order },
      { headers: this.headers }
    );
  }

  listDocuments(params?: { status?: number; type?: number }): Observable<Document[]> {
    let httpParams = new HttpParams();
    if (params?.status) {
      httpParams = httpParams.set('status', String(params.status));
    }
    if (params?.type) {
      httpParams = httpParams.set('type', String(params.type));
    }
    return this.http.get<Document[]>(`${this.baseUrl}/api/documents/documents/`, { headers: this.headers, params: httpParams })
      .pipe(map((res: any) => this.unwrapList<Document>(res)));
  }

  getDocument(id: number): Observable<Document> {
    return this.http.get<Document>(`${this.baseUrl}/api/documents/documents/${id}/`, { headers: this.headers });
  }

  createFromTemplate(data: {
    title: string;
    type_id: number;
    template_id: number;
    status_code?: string;
    context?: any;
    category_ids?: number[];
  }): Observable<Document> {
    return this.http.post<Document>(
      `${this.baseUrl}/api/documents/documents/from-template/`,
      data,
      { headers: this.headers }
    );
  }

  updateDocument(id: number, data: Partial<Document>): Observable<Document> {
    return this.http.patch<Document>(`${this.baseUrl}/api/documents/documents/${id}/`, data, { headers: this.headers });
  }

  createDocumentBlock(data: Partial<DocumentBlock> & { document: number }): Observable<DocumentBlock> {
    return this.http.post<DocumentBlock>(`${this.baseUrl}/api/documents/document-blocks/`, data, { headers: this.headers });
  }

  updateDocumentBlock(id: number, data: Partial<DocumentBlock>): Observable<DocumentBlock> {
    return this.http.patch<DocumentBlock>(`${this.baseUrl}/api/documents/document-blocks/${id}/`, data, { headers: this.headers });
  }

  deleteDocumentBlock(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/api/documents/document-blocks/${id}/`, { headers: this.headers });
  }

  reorderDocumentBlocks(documentId: number, order: Array<{ id: number; position: number }>): Observable<any> {
    return this.http.patch(
      `${this.baseUrl}/api/documents/documents/${documentId}/reorder-blocks/`,
      { order },
      { headers: this.headers }
    );
  }

  renderDocument(documentId: number, context_override?: any): Observable<{ rendered_html: string; render_hash: string }> {
    return this.http.post<{ rendered_html: string; render_hash: string }>(
      `${this.baseUrl}/api/documents/documents/${documentId}/render/`,
      { context_override },
      { headers: this.headers }
    );
  }

  freezeDocument(documentId: number): Observable<Document> {
    return this.http.post<Document>(
      `${this.baseUrl}/api/documents/documents/${documentId}/freeze/`,
      {},
      { headers: this.headers }
    );
  }
}
