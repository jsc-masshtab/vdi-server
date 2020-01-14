import { IParams } from '../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';



@Injectable()
export class UsersService  {

    public paramsForGetUsers: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllUsers(): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql` query users($ordering:String) {
                            users(ordering: $ordering) {
                                id,
                                username,
                                email,
                                last_name,
                                first_name,
                                date_joined,
                                date_updated,
                                last_login,
                                is_superuser,
                                is_active
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetUsers.nameSort
            }
        });
    }

    public getUser(id): Observable<any> {
        return this.service.watchQuery({
            query: gql` query users($id:UUID!) {
                            user(id: $id) {
                                id,
                                username,
                                email,
                                last_name,
                                first_name,
                                date_joined,
                                date_updated,
                                last_login,
                                is_superuser,
                                is_active
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id: `${id}`
            }
        }).valueChanges.pipe(map(data => data.data));
    }

    public createUser(props) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation users(
                                $username: String!,
                                $password: String!,
                                $email: String!,
                                $last_name: String!,
                                $first_name: String!,
                                $is_superuser: Boolean
                            ){
                                createUser(
                                    ${Object.keys(props).map((key) => {
                                        return `${key} :$${key}`;
                                    })}
                                ){
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                ...props
            }
        });
    }

    public updateUser(params, fields) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation users(${params.args}) {
                                updateUser(${params.call}) {
                                        ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                ...params.props,
                ...fields
            }
        });
    }

    public changeUserPassword(params, fields) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation users(${params.args}) {
                                changeUserPassword(${params.call}) {
                                        ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                ...params.props,
                ...fields
            }
        });
    }

    public mutate(params) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation users(${params.args}) {
                    ${params.method}(${params.call}) {
                        ok
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...params.props
            }
        });
    }
}
