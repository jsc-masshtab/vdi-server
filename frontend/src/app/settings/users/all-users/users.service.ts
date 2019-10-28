import { IParams } from './../../../../../types/index.d';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class UsersService  {

    public paramsForGetUsers: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined,
        reverse: undefined
    };

    constructor(private service: Apollo) {}

    public getAllUsers(): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql` query allUsers($ordering:String, $reversed_order: Boolean) {
                            users(ordering: $ordering, reversed_order: $reversed_order) {
                                username
                                date_joined
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetUsers.nameSort,
                reversed_order: this.paramsForGetUsers.reverse
            }
        });
    }

    public createUser(name: string, pass: string) {
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
                username: name,
                password: pass
            }
        });
    }
}