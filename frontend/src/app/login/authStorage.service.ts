import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root',
})

export class AuthStorageService {

    public isLoggedIn: boolean = true;

    constructor() {}

    public checkLogin() {
        this.isLoggedIn = true;
    }

}
