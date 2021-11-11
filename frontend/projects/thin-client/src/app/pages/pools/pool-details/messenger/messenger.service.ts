import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { environment } from 'environments/environment';


@Injectable({
providedIn: 'root'
})
export class MessengerService {
    private url = `${environment.api}client/`;


    constructor(private http: HttpClient ) {
        }

    public sendMessageToAdmin( message: string) {
        return this.http.post(`${this.url}send_text_message`, {msg_type: 'text_msg', message});
    }
}
