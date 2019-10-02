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

    public createUser(username: string,password: string) {
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation AddUser($username: String,$password: String) {
                                createUser(username: $username, password: $password) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                username: username,
                password: password
            }
        })
    }
}