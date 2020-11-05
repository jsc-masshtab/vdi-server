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
            query: gql`
                query controllers {
                    controllers {
                        id
                        verbose_name
                        description
                        address
                        version
                        status
                        verbose_name
                    }
                }
            `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetControllers.nameSort
            }
        });
    }

    public getController(id: string) {
        return this.service.watchQuery({
            query: gql`
                query controllers($id: UUID) {
                    controller(id_: $id) {
                        id
                        verbose_name
                        address
                        description
                        status
                        version
                        token
                    }
                }
            `,
            variables: {
                method: 'GET',
                id
            }
        }).valueChanges;
    }

    public updateController(id, data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation controllers(
                    $id: UUID!,
                    $verbose_name: String,
                    $description: String,
                    $address: String,
                    $token: String) {
                    updateController(
                        id_: $id,
                        verbose_name: $verbose_name,
                        description: $description,
                        address: $address,
                        token: $token) {
                        controller {
                            id
                            verbose_name
                            description
                            address
                            status
                        }
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...id,
                ...data
            }
        });
    }

    public addController(data) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation controllers(
                    $address: String!
                    $verbose_name: String!
                    $token: String!
                    $description: String) {
                    addController(
                        address: $address
                        verbose_name: $verbose_name
                        token: $token
                        description: $description) {
                        controller {
                            id
                            verbose_name
                            description
                            address
                            status
                        }
                    }
                }
            `,
            variables: {
                method: 'POST',
                ...data
            }
        });
    }

    public testController(id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation controllers($id: UUID!) {
                    testController(id_: $id) {
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

    public removeController(id: string) {
        return this.service.mutate<any>({
            mutation: gql`
                mutation controllers($id: UUID!) {
                    removeController(id_: $id) {
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
