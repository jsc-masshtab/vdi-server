import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class ServersService  {

    constructor(private service: Apollo) {}

    public getAllControllers(): QueryRef<any,any> {
       return  this.service.watchQuery({
            query:  gql` query allControllers {
                            controllers {
                                ip
                                description
                            }
                        }
            
                    `,
            variables: {
                method: 'GET'
            }
        }) 
    }

    public addController(ip:string, description:string) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddController($description: String!,$ip: String!) {
                                addController(description: $description,ip: $ip) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                description: description,
                ip: ip
            }
        })
    }
}
