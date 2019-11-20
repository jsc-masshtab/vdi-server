import { IParams } from './../../../../../types/index.d';
import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';


@Injectable()
export class DatapoolsService {

    public paramsForGetDatapools: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
        spin: true,
        nameSort: undefined,
        reverse: undefined
    };

    constructor(private service: Apollo) {}

    public getAllDatapools(): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query allDatapools($ordering:String, $reversed_order: Boolean) {
                            datapools(ordering: $ordering, reversed_order: $reversed_order) {
                                id
                                used_space
                                free_space
                                status
                                type
                                vdisk_count
                                file_count
                                iso_count
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                ordering: this.paramsForGetDatapools.nameSort,
                reversed_order: this.paramsForGetDatapools.reverse
            }
        });
    }

    public getDatapool(id: string): QueryRef<any, any> {
        return  this.service.watchQuery({
            query:  gql` query Datapool($id: String) {
                            datapool(id: $id) {
                                used_space
                                free_space
                                size
                                status
                                type
                                vdisk_count
                                file_count
                                iso_count
                                verbose_name
                            }
                        }
                    `,
            variables: {
                method: 'GET',
                id
            }
        });
    }
}


