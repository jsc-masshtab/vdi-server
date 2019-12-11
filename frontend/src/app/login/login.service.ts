import { Observable } from 'rxjs';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';


@Injectable()
export class LoginService {

    constructor(private http: HttpClient) {}

    public auth(authData: {username: string, password: string}): Observable<any> {
        let url = 'http://192.168.20.110/api/auth';

        let headers = new HttpHeaders({
            'Content-Type': 'application/json'
        });

        return this.http.post(url, JSON.stringify(authData), { headers });
    }
}
