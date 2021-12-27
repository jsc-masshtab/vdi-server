import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';


import { environment } from 'environments/environment';
import { IResponse } from '../../interfaces/https';

interface UserData {
    ok: boolean
    user: {
        two_factor: boolean
    }
}

@Injectable({
    providedIn: 'root'
})
export class UserService {
    private url = `${environment.api}client`;
    
    constructor(private http: HttpClient){}


    public getUserData(): Observable<IResponse<UserData>> {
        return this.http.get<IResponse<UserData>>(`${this.url}/get_user_data/?`)    }

    public updateUserData(two_factor: boolean): Observable<IResponse<UserData>>{
        return this.http.post<IResponse<UserData>>(`${this.url}/update_user_data/?`, {two_factor})
    }

}
