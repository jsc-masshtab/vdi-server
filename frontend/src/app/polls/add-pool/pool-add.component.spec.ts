import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PoolAddComponent } from './pool-add.component';

describe('PoolAddComponent', () => {
  let component: PoolAddComponent;
  let fixture: ComponentFixture<PoolAddComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PoolAddComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PoolAddComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
