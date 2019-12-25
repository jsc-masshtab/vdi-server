import { environment } from './../../environments/environment.demo';
import { AuthStorageService } from './authStorage.service';
import { Observable } from 'rxjs';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';


@Injectable()
export class LoginService {

    constructor(private http: HttpClient, private authStorageService: AuthStorageService) {}

    public auth(authData: {username: string, password: string}): Observable<any> {
        let url = `${environment.url}auth`;

        let headers = new HttpHeaders({
            'Content-Type': 'application/json'
        });

        return this.http.post(url, JSON.stringify(authData), { headers });
    }

    public logout(): Observable<any> {
        let url = `${environment.url}logout`;
        let headers = new HttpHeaders().set('Content-Type', 'application/json')
                                       .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`);

        return this.http.post(url, {}, { headers });
    }
}
