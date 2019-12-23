import { IParams } from '../../../../../../types';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class ControllersService {

    public paramsForGetControllers: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}


    public getAllControllers(): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql` query controllers {
                            controllers {
                                id
                                verbose_name
                                description
                                address
                                version
                                status
                                username
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetControllers.nameSort
            }
        });
    }

    public addController({address, description, username, verbose_name, password }) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation controllers($description: String,$address: String!,
                                $username: String!,$verbose_name: String!,
                                $ldap_connection: Boolean!,$password: String!) {
                                addController(description: $description,address: $address,
                                                username: $username,verbose_name: $verbose_name,
                                                ldap_connection: $ldap_connection,password: $password) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                description,
                address,
                username,
                verbose_name,
                password,
                ldap_connection: false
            }
        });
    }

    public removeController(id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation controllers($id: UUID!) {
                                removeController(id: $id) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                id
            }
        });
    }
}
