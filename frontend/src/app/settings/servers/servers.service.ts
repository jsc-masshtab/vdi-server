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
                            mutation AddController($ip: String!,$description: String!) {
                                addController(ip: $ip, description: $description) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                ip: ip,
                description: description
            }
        })
    }
}
