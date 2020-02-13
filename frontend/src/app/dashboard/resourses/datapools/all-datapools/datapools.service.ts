import { IParams } from '../../../../../../types';
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class DatapoolsService {

    public paramsForGetDatapools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined
    };

    constructor(private service: Apollo) {}

    public getAllDatapools(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query resources($ordering:String, $take_broken: Boolean) {
                            datapools(ordering: $ordering, take_broken: $take_broken) {
                                id
                                used_space
                                free_space
                                status
                                type
                                verbose_name
                                controller {
                                    address
                                }
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetDatapools.nameSort,
                take_broken: true
            }
        });
    }

    public getDatapool(id: string, controller_address: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query resources($id: String, $controller_address: String) {
                            datapool(id: $id, controller_address: $controller_address) {
                                used_space
                                free_space
                                size
                                status
                                type
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id,
                controller_address
            }
        });
    }
}


