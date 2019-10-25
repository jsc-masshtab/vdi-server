import { IParams } from './../../../../../types/index.d';
import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class ControllersService  {

    public paramsForGetControllers: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined,
        reverse: undefined
    };

    constructor(private service: Apollo) {}

    public getAllControllers(): QueryRef<any, any> {
       return  this.service.watchQuery({
            query:  gql` query allControllers($ordering:String, $reversed_order: Boolean) {
                            controllers(ordering: $ordering, reversed_order: $reversed_order) {
                                ip
                                description
                                status
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetControllers.nameSort,
                reversed_order: this.paramsForGetControllers.reverse
            }
        });
    }

    public addController(ipController: string, descriptionController: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation AddController($description: String,$ip: String!) {
                                addController(description: $description,ip: $ip) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                description: descriptionController,
                ip: ipController
            }
        });
    }

    public removeController(ip: string) {
        return this.service.mutate<any>({
            mutation: gql`
                            mutation RemoveController($controller_ip: String) {
                                removeController(controller_ip: $controller_ip) {
                                    ok
                                }
                            }
            `,
            variables: {
                method: 'POST',
                controller_ip: ip
            }
        });
    }
}
