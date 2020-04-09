import { Injectable } from '@angular/core';
import { HttpClient, HttpRequest } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class LicenseService {

  constructor(private http: HttpClient) { }

  public getLicence(): any {
    return this.http.get('/api/license/');
  }

  public upload(url, file) {
    const req = new HttpRequest('POST', url, file, {
      reportProgress: true,
    });

    return this.http.request(req);
  }
}
