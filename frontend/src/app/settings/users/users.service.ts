import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class UsersService  {

    constructor(private service: Apollo) {}

    public getAllUsers(): QueryRef<any,any> {
       return  this.service.watchQuery({
            query:  gql` query allUsers {
                            users {
                                username
                            }
                        }
                    `,
            variables: {
                method: 'GET'
            }
        }) 
    }
}
