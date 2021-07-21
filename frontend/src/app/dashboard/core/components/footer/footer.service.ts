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
          events($start_date: DateTime, $end_date: DateTime) {
            all: count(start_date: $start_date, end_date: $end_date),
            warning: count(event_type: 1, start_date: $start_date, end_date: $end_date),
            error: count(event_type: 2, start_date: $start_date, end_date: $end_date)
          }
        `,
        variables: {
            method: 'GET',
            start_date: new Date(0).toISOString(),
            end_date: new Date().toISOString()
        }
    });
  }
}
