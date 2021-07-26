import { HttpClient, HttpRequest, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { AuthStorageService } from 'src/app/pages/login/authStorage.service';

@Injectable({
  providedIn: 'root'
})
export class LicenseService {

  constructor(private http: HttpClient, private authStorageService: AuthStorageService) { }

  public getLicence(): any {
    let headers = new HttpHeaders().set('Content-Type', 'application/json')
    .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
    .set('Client-Type', 'angular-web');

    return this.http.get('/api/license/', { headers });
  }

  public upload(url, file) {
    let headers = new HttpHeaders()
    .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
    .set('Client-Type', 'angular-web');

    const req = new HttpRequest('POST', url, file, {
      reportProgress: true,
      headers
    });

    return this.http.request(req);
  }
}
