import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { ClustersComponent } from './clusters.component';
import { ClustersService } from './clusters.service';
import { of } from 'rxjs';

describe('ClustersComponent', () => {
  let component: ClustersComponent;
  let fixture: ComponentFixture<ClustersComponent>;

  let serviceStub: Partial<ClustersService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getAllClusters(): any {
        return {
          valueChanges: of({
            data: {
              clusters: []
            }
          }),
          refetch() {}
        };
      },
      paramsForGetClusters: {
        spin: false
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [ ClustersComponent ],
      providers: [
        {
          provide: ClustersService,
          useValue: serviceStub
        }
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ClustersComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
