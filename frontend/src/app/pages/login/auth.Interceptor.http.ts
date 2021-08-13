import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse, HttpResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import { AuthStorageService } from './authStorage.service';

export class AuthInterceptor implements HttpInterceptor {

    constructor(private authStorageService: AuthStorageService) { }

    public intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        const authReq = req.clone({
            headers: req.headers.set('Accept-Language', 'ru')
        });

        return next.handle(authReq).pipe(
            tap(event => {
                if (event instanceof HttpResponse) { return; }
            }, err => {
                    if (err instanceof HttpErrorResponse) {
                    if (err.status === 401) { this.authStorageService.logout(); }
                }
            }));
    }
}
