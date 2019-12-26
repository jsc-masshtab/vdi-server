import { AuthStorageService } from './../../../login/authStorage.service';
import { Observable } from 'rxjs';

import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse, HttpResponse } from '@angular/common/http';
import { tap } from 'rxjs/operators';

export class AuthInterceptor implements HttpInterceptor {

    constructor( private authStorageService: AuthStorageService) {}

    public intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const authReq = req.clone();

    return next.handle(authReq).pipe(
        tap(event => {
        if (event instanceof HttpResponse)  {
            console.log('Server response');
        }
        }, err => {
        if (err instanceof HttpErrorResponse) {
            if (err.status === 401) { this.authStorageService.logout(); }
        }}));
    }
 }
