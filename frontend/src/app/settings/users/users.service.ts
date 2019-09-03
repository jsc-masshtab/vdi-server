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

    public entitleUsersToPool(pool_id: number,entitled_users: []) {
        console.log(pool_id,entitled_users);
        return this.service.mutate<any>({
            mutation: gql`  
                            mutation EntitleUsersToPool($pool_id: ID,$entitled_users: [ID]) {
                                entitleUsersToPool(pool_id: $pool_id, entitled_users: $entitled_users) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                pool_id: pool_id,
                entitled_users: entitled_users
            }
        })
    }
}
