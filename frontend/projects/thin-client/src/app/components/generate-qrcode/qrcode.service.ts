import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';


import { environment } from 'environments/environment';
import { IResponse } from '../../interfaces/https';



interface QRCode {
    secret: string
    qr_uri: string
}



@Injectable({
    providedIn: 'root'
})
export class QRCodeService {
    private url = `${environment.api}client`;
    
    constructor(private http: HttpClient){}

    public generateQRCode(): Observable<IResponse<QRCode>> {
        return this.http.post<IResponse<QRCode>>(`${this.url}/generate_user_qr_code/?`, {});
    }

}
