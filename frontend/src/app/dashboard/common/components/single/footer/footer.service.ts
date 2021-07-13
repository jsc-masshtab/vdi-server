import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthStorageService } from 'src/app/login/authStorage.service';
import { Subject } from 'rxjs';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

@Injectable({
  providedIn: 'root'
})
export class FooterService {

  private channel = new Subject();
  channel$ = this.channel.asObservable();

  constructor(private http: HttpClient, private authStorageService: AuthStorageService, private service: Apollo) { }

  public getInfo(): any {
    return this.http.get('/api/version/');
  }

  public getLicence(): any {
    let headers = new HttpHeaders().set('Content-Type', 'application/json')
    .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
    .set('Client-Type', 'angular-web');

    return this.http.get('/api/license/', { headers });
  }

  reload() {
    this.channel.next();
  }

  public countEvents(): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query
          events {
            count
            warning: count(event_type: 1),
            error: count(event_type: 0)
          }
        `
    });
  }
}
