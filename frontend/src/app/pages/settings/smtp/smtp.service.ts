import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


export interface ISmtpResponse {
  smtpSettings: ISmtpSettings
}

export interface ISmtpSettings {
  hostname: string | null
  port: number
  SSL: boolean
  TLS: boolean
  fromAddress: string | null
  user: string | null
  password: string | null,
  level: number
}

export interface ISmtpMutationResponse {
  changeSmtpSettings: IChangeSmtpSettings
}

interface IChangeSmtpSettings {
  ok: boolean
}

@Injectable({
  providedIn: 'root'
})
export class SmtpService {

  constructor(private apollo: Apollo) { }

  public getSmptSettings(): QueryRef<ISmtpResponse> {
    return this.apollo.watchQuery({
      query: gql`
        query settings {
          smtpSettings: smtp_settings {
            hostname
            port
            password
            fromAddress: from_address
            user
            SSL
            TLS
            level
          }
        }
      `,
      variables: {
        method: 'GET'
      }
    });
  }


  public changeSmtpSettings(data: ISmtpSettings) {
    return this.apollo.mutate<ISmtpMutationResponse>({
      mutation: gql`
        mutation settings($hostname: ShortString, $port: Int, $password: ShortString, $fromAddress: ShortString, $user: ShortString, $level: Int, $SSL: Boolean, $TLS: Boolean) {
          changeSmtpSettings (hostname: $hostname, port:$port, password: $password, from_address: $fromAddress, user: $user, level: $level, SSL: $SSL, TLS: $TLS ){
           ok
         }
      }`,
      variables: {
        method: 'POST',
        ...data
      }
    })
  }

}
