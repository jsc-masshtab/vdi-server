import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse, HttpResponse, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import { ErrorsService } from '../errors/errors.service';
import { AuthStorageService } from './authStorage.service';

export class AuthInterceptor implements HttpInterceptor {

    constructor(private authStorageService: AuthStorageService, private errorService: ErrorsService) { }

    public intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        const authReq = req.clone({
            headers: new HttpHeaders({
                'Content-Type':  'application/json',
                Authorization: `jwt ${this.authStorageService.getItemStorage('token')}`,
                'Client-Type': 'application/json'
            })
        });

        return next.handle(authReq).pipe(
            tap(event => {
                if (event instanceof HttpResponse) { 
                    if (event.body && event.body.errors){
                        this.errorService.setError(event.body.errors);
                    }
                    return;
                     }
            }, err => {
                    if (err instanceof HttpErrorResponse) {                        
                        this.errorService.setError(err.error.errors);
                        if (err.status === 401) { this.authStorageService.logout(); }
                }
            }));
    }
}
