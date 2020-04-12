import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class FooterService {

  constructor(private http: HttpClient) { }

  public getInfo(): any {
    return this.http.get('/api/version/');
  }

  public getLicence(): any {
    return this.http.get('/api/license/');
  }
}
