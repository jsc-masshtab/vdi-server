import { Router } from '@angular/router';
import { Injectable } from '@angular/core';
import { JwtHelperService } from '@auth0/angular-jwt';

@Injectable({
    providedIn: 'root',
})

export class AuthStorageService {

    private jwt: JwtHelperService;

    constructor(private router: Router) { this.jwt = new JwtHelperService(); }
// isTokenExpired() === false - не истек

    public checkLogin(): boolean {
        let token: string = this.getToken();
        if (token && !this.jwt.isTokenExpired(token)) {
            return true;
        } else {
            this.router.navigate(['login']);
            return false;
        }
    }

    public saveToken(token: {access_token: string, expires_on: string}): void {
        localStorage.setItem('token', token.access_token);
    }

    private getToken(): string | null {
        return localStorage.getItem('token') || null;
    }

}

