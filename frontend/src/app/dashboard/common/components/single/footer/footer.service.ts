import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthStorageService } from 'src/app/login/authStorage.service';
import { Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class FooterService {

  private channel = new Subject();
  channel$ = this.channel.asObservable();

  constructor(private http: HttpClient, private authStorageService: AuthStorageService) { }

  public getInfo(): any {
    return this.http.get('/api/version/');
  }

  public getLicence(): any {
    let headers = new HttpHeaders().set('Content-Type', 'application/json')
    .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
    .set('Client-Type', 'angular-web');

    return this.http.get('/api/license/', { headers });
  }

  reload() {
    this.channel.next();
  }
}
