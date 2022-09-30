import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { AuthStorageService } from '../login/authStorage.service';

@Injectable()
export class MainService  {
  constructor(
    private appolo: Apollo,
    private http: HttpClient,
    private authStorageService: AuthStorageService
  ) {}

  public getVersionClientInfo(): QueryRef<any, any> {
    return this.appolo.watchQuery({
      query: gql`
        query broker_info {
          version_client: minimum_supported_desktop_thin_client_version
        }
      `,
      variables: {
        method: 'GET'
      },
      fetchPolicy: 'network-only'
    });
  }

  public getPoolsInfo(): QueryRef<any, any> {
    return this.appolo.watchQuery({
      query: gql`
        query pools {

          pools {
            pool_id
            pool_type
            verbose_name
            vm_amount
            users_count
          }   
        }
      `,
      variables: {
        method: 'GET'
      },
      fetchPolicy: 'network-only'
    });
  }

  public getControllersInfo(): QueryRef<any, any> {
    return this.appolo.watchQuery({
      query: gql`
        query controllers {

          controllers {
            id
            verbose_name
          }
        }
      `,
      variables: {
        method: 'GET'
      },
      fetchPolicy: 'network-only'
    });
  }

  public getLicence(): any {
    let headers = new HttpHeaders().set('Content-Type', 'application/json')
    .set('Authorization', `jwt ${this.authStorageService.getItemStorage('token')}`)
    .set('Client-Type', 'angular-web');

    return this.http.get('/api/license/', { headers });
  }

  public getVersionInfo(): any {
    return this.http.get('/api/version/');
  }
}

