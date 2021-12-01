import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { environment } from '../../../environments/environment';
import { AuthStorageService } from './authStorage.service';


export interface ISettings {
    language: string
    ldap: string
}
@Injectable()
export class LoginService {

    constructor(private http: HttpClient, private authStorageService: AuthStorageService) {}

    public auth(authData: {username: string, password: string}): Observable<any> {
        let url = `${environment.api}auth`;

        let headers = new HttpHeaders({
            'Content-Type': 'application/json'
        }).set('Client-Type', 'angular-web');

        return this.http.post(url, JSON.stringify(authData), { headers });
    }

    public logout(): Observable<any> {
        let url = `${environment.api}logout`;
        let headers = new HttpHeaders().set('Content-Type', 'application/json')
                                       .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
                                       .set('Client-Type', 'angular-web');

        return this.http.post(url, {}, { headers });
    }




    public getSettings(): Observable<ISettings> {
        return this.http.get<ISettings>('/api/sso/').pipe(map((res: any) => res.data));
      }
}
