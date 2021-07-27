import { HttpClient, HttpRequest, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/internal/Subject';
import { map } from 'rxjs/operators';
import { AuthStorageService } from 'src/app/pages/login/authStorage.service';


export interface ICopyrightResponse{
  data: ICopyrightData
}

export interface ICopyrightData {
  copyright: string
  url: string
  version: string
  year: string
}

@Injectable({
  providedIn: 'root'
})
export class LicenseService {

  private channel = new Subject();
  channel$ = this.channel.asObservable();
  
  constructor(private http: HttpClient, private authStorageService: AuthStorageService) { }

  public getLicence(): any {
    let headers = new HttpHeaders().set('Content-Type', 'application/json')
    .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
    .set('Client-Type', 'angular-web');

    return this.http.get('/api/license/', { headers });
  }

  public uploadFile(url, file) {
    let headers = new HttpHeaders()
    .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
    .set('Client-Type', 'angular-web');

    const req = new HttpRequest('POST', url, file, {
      reportProgress: true,
      headers
    });

    return this.http.request(req);
  }

  public reload(): void {
    this.channel.next();
  }

  public getCopyrightInfo(): Observable<ICopyrightData> {
    return this.http.get<ICopyrightResponse>('/api/version/').pipe(map(res=> res.data));
  }
}
