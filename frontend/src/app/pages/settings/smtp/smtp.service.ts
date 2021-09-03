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




@Injectable({
  providedIn: 'root'
})
export class SmtpService {

  constructor(private appolo: Apollo) { }

  public getSmptSettings(): QueryRef<ISmtpResponse> {
    return this.appolo.watchQuery({
      query: gql`
        query settings {
          smtpSettings: smtp_settings {
            hostname
            port
            SSL
            TLS
            fromAdress: from_address
            user
            password
          }
        }
      `,
      variables: {
        method: 'GET'
      }
    });
  }


  // public changeSmtpSettings(data: modalData) {
  //   return this.apollo.mutate<IMutationResponse>({
  //     mutation: gql`
  //       mutation settings($password: String, $serviceName:String, $actionType: ServiceAction) {
  //       doServiceAction(sudo_password:$password, service_name: $serviceName, service_action: $actionType){
  //          ok,
  //          service_status
  //        }
  //     }`,
  //     variables: {
  //       method: 'POST',
  //       password: data.password,
  //       serviceName: data.serviceName,
  //       actionType: data.actionType
  //     }
  //   })
  // }

}
